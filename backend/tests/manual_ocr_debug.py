import asyncio
import os
import sys
import fitz  # PyMuPDF

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from infrastructure.ocr.ocr_service_impl import MultiProviderOCRService

def pdf_to_image(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better quality
    return pix.tobytes("jpeg")

async def main():
    ocr = MultiProviderOCRService()
    
    files = [
        "../docs/acta_matrimonio.pdf",
        "../docs/certificado_negativo_anses.pdf"
    ]
    
    for f in files:
        if not os.path.exists(f):
            print(f"File not found: {f}")
            continue
            
        print(f"\n{'='*50}")
        print(f"Processing: {f}")
        print(f"{'='*50}")
        
        try:
            img_bytes = pdf_to_image(f)
            
            # 1. Try Marriage Cert Extraction
            print("\n--- Attempting Marriage Certificate Extraction ---")
            marriage_res = await ocr.extract_marriage_certificate_data(img_bytes)
            print(f"Success: {marriage_res.success}")
            print(f"Confidence: {marriage_res.confidence}")
            print(f"Data: {marriage_res.data}")
            print(f"Errors: {marriage_res.errors}")
            
            # 2. Try ANSES Extraction
            print("\n--- Attempting ANSES Extraction ---")
            anses_res = await ocr.extract_anses_data(img_bytes)
            print(f"Success: {anses_res.success}")
            print(f"Confidence: {anses_res.confidence}")
            print(f"Data: {anses_res.data}")
            print(f"Errors: {anses_res.errors}")

            # 3. Try Generic Extraction (for classification simulation)
            print("\n--- Attempting Generic Extraction ---")
            generic_res = await ocr.extract_generic_document(img_bytes)
            text = generic_res.data.get("text", "")
            print(f"Text length: {len(text)}")
            print(f"Text preview: {text[:200]}...")
            
            # Simulate classification logic
            text_lower = text.lower()
            if anses_res.success:
                 print("-> CLASSIFIED AS: ANSES Certificate (Structured)")
            elif any(k in text_lower for k in ["anses", "certificacion negativa", "certificación negativa"]):
                print("-> CLASSIFIED AS: ANSES Certificate (Keyword)")
            elif any(k in text_lower for k in ["acta", "matrimonio", "registro civil"]):
                print("-> CLASSIFIED AS: Marriage Certificate (by keywords)")
            else:
                print("-> CLASSIFIED AS: Unknown")
                
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
