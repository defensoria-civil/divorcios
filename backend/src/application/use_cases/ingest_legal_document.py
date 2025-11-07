"""
Use Case: Ingestión de Documentos Legales

Procesa documentos legales y los almacena en la base de conocimiento
con sus embeddings para búsqueda semántica.
"""
from sqlalchemy.orm import Session
from typing import List
import structlog
from dataclasses import dataclass

from infrastructure.persistence.models import SemanticKnowledge
from infrastructure.ai.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class IngestedDocument:
    """Resultado de la ingestión de un documento"""
    title: str
    chunks_created: int
    success: bool


class IngestLegalDocumentUseCase:
    """
    Ingesta documentos legales en la base de conocimiento.
    
    Proceso:
    1. Divide el contenido en chunks de tamaño adecuado
    2. Genera embeddings para cada chunk
    3. Almacena en la base de datos con metadata
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMRouter()
        self.max_chunk_size = 500  # tokens aproximados
    
    async def execute(self, title: str, content: str, category: str = "legislacion") -> IngestedDocument:
        """
        Ingesta un documento legal.
        
        Args:
            title: Título del documento
            content: Contenido completo del documento
            category: Categoría (legislacion, jurisprudencia, doctrina)
        
        Returns:
            IngestedDocument con resultado de la operación
        """
        try:
            logger.info("ingest_document_started", title=title, category=category)
            
            # 1. Dividir en chunks
            chunks = self._chunk_text(content)
            logger.info("document_chunked", chunks=len(chunks))
            
            # 2. Generar embeddings
            embeddings = await self.llm.embed(chunks)
            logger.info("embeddings_generated", count=len(embeddings))
            
            # 3. Almacenar en la base de datos
            chunks_created = 0
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                knowledge = SemanticKnowledge(
                    title=f"{title} - Parte {i+1}/{len(chunks)}",
                    content=chunk,
                    embedding=embedding
                )
                self.db.add(knowledge)
                chunks_created += 1
            
            self.db.commit()
            
            logger.info(
                "ingest_document_completed",
                title=title,
                chunks=chunks_created
            )
            
            return IngestedDocument(
                title=title,
                chunks_created=chunks_created,
                success=True
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error("ingest_document_failed", title=title, error=str(e))
            return IngestedDocument(
                title=title,
                chunks_created=0,
                success=False
            )
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Divide el texto en chunks manejables.
        
        Estrategia:
        - Divide por párrafos primero
        - Si un párrafo es muy largo, lo divide por oraciones
        - Mantiene tamaño máximo de ~500 tokens (aprox 2000 caracteres)
        """
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        max_chars = 2000  # Aproximadamente 500 tokens
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Si el párrafo es muy largo, dividirlo
            if len(paragraph) > max_chars:
                # Dividir por oraciones
                sentences = paragraph.replace('. ', '.|').split('|')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_chars:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence
            else:
                # Si agregar este párrafo excede el límite, guardar el chunk actual
                if len(current_chunk) + len(paragraph) > max_chars:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph
        
        # Agregar el último chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
