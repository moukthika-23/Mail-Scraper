import asyncio
import os
from app.core.config import settings
from app.services.search_service import perform_rag_search

async def main():
    user_id = "test-user-id" # fake user id just to see if it crashes before DB call
    try:
        res = await perform_rag_search("test query", user_id)
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
