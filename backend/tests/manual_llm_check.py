import asyncio
import sys
from pathlib import Path

# Asegurar que 'src' esté en sys.path cuando se ejecuta fuera de Docker
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.ai.router import LLMRouter


async def main() -> None:
    router = LLMRouter()

    print("=== LLM chat check (router.chat) ===")
    try:
        resp = await router.chat(
            messages=[{"role": "user", "content": "Hola, ¿puedes responder brevemente?"}]
        )
        print("CHAT OK:\n", resp[:300], "..." if len(resp) > 300 else "")
    except Exception as e:
        print("CHAT ERROR:", repr(e))

    print("\n=== LLM embeddings check (router.embed) ===")
    try:
        emb = await router.embed(["texto de prueba para embeddings"])
        if emb and isinstance(emb, list) and isinstance(emb[0], list):
            print("EMBEDDINGS OK: dim =", len(emb[0]), "primeros valores:", emb[0][:5])
        else:
            print("EMBEDDINGS RESPONSE CON FORMATO INESPERADO:", type(emb))
    except Exception as e:
        print("EMBEDDINGS ERROR:", repr(e))


if __name__ == "__main__":
    asyncio.run(main())

