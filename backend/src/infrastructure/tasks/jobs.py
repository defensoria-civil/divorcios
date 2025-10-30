from .celery_app import app

@app.task
def example_ocr_task(file_path: str) -> dict:
    # Placeholder for OCR processing
    return {"status": "processed", "file": file_path}
