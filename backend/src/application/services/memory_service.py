from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from infrastructure.persistence.models import Memory, SemanticKnowledge
from infrastructure.persistence.repositories import MemoryRepository
from infrastructure.ai.router import LLMRouter
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

class MemoryService:
    """
    Servicio de memoria contextual avanzada
    Implementa 4 tipos de memoria:
    - Inmediata: Últimos 10 mensajes
    - Sesión: Datos de la conversación actual
    - Episódica: Historial de conversaciones pasadas
    - Semántica: Conocimiento legal estructurado
    """
    
    def __init__(self, db: Session, llm: Optional[LLMRouter] = None):
        self.db = db
        self.memory_repo = MemoryRepository(db)
        self.llm = llm or LLMRouter()
    
    async def store_immediate_memory(self, case_id: int, content: str):
        """Almacena memoria inmediata (últimos mensajes)"""
        self.memory_repo.add_memory(case_id, "immediate", content)
        
        # Mantener solo últimos 10
        memories = self.db.query(Memory).filter(
            Memory.case_id == case_id,
            Memory.kind == "immediate"
        ).order_by(Memory.created_at.desc()).all()
        
        if len(memories) > 10:
            for mem in memories[10:]:
                self.db.delete(mem)
            self.db.commit()
    
    async def store_session_memory(self, case_id: int, key: str, value: Any):
        """Almacena datos de sesión como JSON"""
        import json
        content = json.dumps({key: value})
        
        # Actualizar o crear
        existing = self.db.query(Memory).filter(
            Memory.case_id == case_id,
            Memory.kind == "session",
            Memory.content.like(f'%"{key}":%')
        ).first()
        
        if existing:
            data = json.loads(existing.content)
            data[key] = value
            existing.content = json.dumps(data)
            self.db.commit()
        else:
            self.memory_repo.add_memory(case_id, "session", content)
    
    async def store_episodic_memory(self, case_id: int, summary: str):
        """Almacena resumen episódico con embedding para búsqueda semántica"""
        # Generar embedding
        embeddings = await self.llm.embed([summary])
        embedding = None
        if embeddings and embeddings[0]:
            emb = embeddings[0]
            # Asegurar vector 1D
            if isinstance(emb, list) and len(emb) > 0 and isinstance(emb[0], list):
                emb = emb[0]
            embedding = emb
        
        mem = Memory(
            case_id=case_id,
            kind="episodic",
            content=summary,
            embedding=embedding
        )
        self.db.add(mem)
        self.db.commit()
        logger.info("episodic_memory_stored", case_id=case_id, summary_length=len(summary))
    
    async def retrieve_immediate_memory(self, case_id: int) -> List[str]:
        """Recupera memoria inmediata (últimos 10 mensajes)"""
        memories = self.db.query(Memory).filter(
            Memory.case_id == case_id,
            Memory.kind == "immediate"
        ).order_by(Memory.created_at.desc()).limit(10).all()
        
        return [m.content for m in reversed(memories)]
    
    async def retrieve_session_data(self, case_id: int) -> Dict[str, Any]:
        """Recupera todos los datos de sesión"""
        import json
        memories = self.db.query(Memory).filter(
            Memory.case_id == case_id,
            Memory.kind == "session"
        ).all()
        
        result = {}
        for mem in memories:
            try:
                data = json.loads(mem.content)
                result.update(data)
            except:
                pass
        
        return result
    
    async def search_episodic_memory(self, case_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Búsqueda semántica en memoria episódica usando embeddings.

        En PostgreSQL se usa pgvector; en otros motores (SQLite en tests) se degrada a un ORDER BY simple.
        """
        # Generar embedding de la query
        embeddings = await self.llm.embed([query])
        if not embeddings or not embeddings[0]:
            return []

        query_embedding = embeddings[0]

        # Si el embedding viene anidado [[...]], aplanarlo
        if isinstance(query_embedding[0], list):
            query_embedding = query_embedding[0]

        # Si no estamos en PostgreSQL, evitar sintaxis pgvector incompatible (como en SQLite)
        if self.db.bind and self.db.bind.dialect.name != "postgresql":  # type: ignore[attr-defined]
            rows = (
                self.db.query(Memory)
                .filter(Memory.case_id == case_id, Memory.kind == "episodic")
                .order_by(Memory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {"id": m.id, "content": m.content, "distance": None}
                for m in rows
            ]

        # Búsqueda vectorial usando pgvector
        # Formato: <-> es el operador de distancia euclidiana
        # Convertir embedding a formato string de PostgreSQL: '[1,2,3]'
        embedding_str = str(query_embedding).replace(' ', '')

        result = self.db.execute(
            text("""
                SELECT id, content,
                       embedding <-> CAST(:query_embedding AS vector) AS distance
                FROM memories
                WHERE case_id = :case_id AND kind = 'episodic'
                ORDER BY distance
                LIMIT :limit
            """),
            {
                "query_embedding": embedding_str,
                "case_id": case_id,
                "limit": limit,
            },
        ).fetchall()

        # Mapear todas las filas devueltas, no solo una. Evita NameError y
        # permite retornar múltiples recuerdos ordenados por distancia.
        return [
            {"id": r[0], "content": r[1], "distance": r[2]}
            for r in result
        ]

    async def search_semantic_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Búsqueda en base de conocimiento legal semántico.

        En PostgreSQL se usa pgvector; en otros motores se degrada a un ORDER BY simple.
        """
        embeddings = await self.llm.embed([query])
        if not embeddings or not embeddings[0]:
            return []

        query_embedding = embeddings[0]

        # Si el embedding viene anidado [[...]], aplanarlo
        if isinstance(query_embedding[0], list):
            query_embedding = query_embedding[0]

        # Si no estamos en PostgreSQL, usar un orden simple sin operador vectorial
        if self.db.bind and self.db.bind.dialect.name != "postgresql":  # type: ignore[attr-defined]
            rows = (
                self.db.query(SemanticKnowledge)
                .order_by(SemanticKnowledge.id.desc())
                .limit(limit)
                .all()
            )
            return [
                {"id": r.id, "title": r.title, "content": r.content, "distance": None}
                for r in rows
            ]

        # Convertir embedding a formato string de PostgreSQL: '[1,2,3]'
        embedding_str = str(query_embedding).replace(' ', '')

        result = self.db.execute(
            text("""
                SELECT id, title, content,
                       embedding <-> CAST(:query_embedding AS vector) AS distance
                FROM semantic_knowledge
                ORDER BY distance
                LIMIT :limit
            """),
            {
                "query_embedding": embedding_str,
                "limit": limit,
            },
        ).fetchall()

        return [
            {"id": row[0], "title": row[1], "content": row[2], "distance": row[3]}
            for row in result
        ]
    
    async def build_context_for_llm(self, case_id: int, current_question: str) -> str:
        """
        Construye contexto completo para el LLM combinando todos los tipos de memoria
        """
        context_parts = []
        
        # 1. Memoria inmediata (últimos mensajes)
        immediate = await self.retrieve_immediate_memory(case_id)
        if immediate:
            context_parts.append("## Conversación reciente:\n" + "\n".join(immediate))
        
        # 2. Datos de sesión
        session_data = await self.retrieve_session_data(case_id)
        if session_data:
            import json
            context_parts.append(f"## Datos del caso:\n{json.dumps(session_data, indent=2, ensure_ascii=False)}")
        
        # 3. Memoria episódica relevante
        episodic = await self.search_episodic_memory(case_id, current_question, limit=3)
        if episodic:
            episodes = "\n".join([f"- {ep['content']}" for ep in episodic])
            context_parts.append(f"## Conversaciones anteriores relevantes:\n{episodes}")
        
        # 4. Conocimiento legal relevante
        knowledge = await self.search_semantic_knowledge(current_question, limit=2)
        if knowledge:
            docs = "\n\n".join([f"**{k['title']}**\n{k['content']}" for k in knowledge])
            context_parts.append(f"## Conocimiento legal aplicable:\n{docs}")
        
        return "\n\n".join(context_parts)
    
    async def summarize_conversation(self, case_id: int) -> str:
        """Genera resumen de conversación para almacenar en memoria episódica"""
        immediate = await self.retrieve_immediate_memory(case_id)
        if not immediate:
            return ""
        
        conversation = "\n".join(immediate)
        
        prompt = f"""Resume la siguiente conversación en 2-3 oraciones clave, 
enfocándote en los datos recopilados y el progreso del trámite:

{conversation}

Resumen:"""
        
        summary = await self.llm.chat([{"role": "user", "content": prompt}])
        return summary.strip()
