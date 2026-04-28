from backend.services.rag_service import rag_service
import asyncio

async def test():
    print("Testing RAG service...")
    try:
        # This will trigger model loading
        res = await rag_service.answer_question("test question", selected_docs=[])
        print("Success!")
        print(res)
    except Exception as e:
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    asyncio.run(test())
