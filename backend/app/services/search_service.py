from groq import Groq
from app.core.config import settings
from app.core.db import supabase
import time

embedding_model = None

# Initialize Groq for LLM orchestration
groq_client = Groq(api_key=settings.GROQ_API_KEY)


def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        from sentence_transformers import SentenceTransformer

        embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return embedding_model

async def perform_rag_search(query: str, user_id: str, top_k: int = 10) -> dict:
    start_time = time.time()
    
    # 1. Embed query (fast CPU execution)
    # 2. Vector Search (Assume RPC exists -> user must execute this SQL in Supabase)
    try:
        query_vector = get_embedding_model().encode(query).tolist()
        search_res = supabase.rpc(
            "match_emails",
            {
                "query_embedding": query_vector,
                "p_user_id": user_id,
                "match_count": top_k
            }
        ).execute()
        results = search_res.data or []
    except Exception as e:
        print(f"[RAG Error] RPC failed: {e}. Falling back to empty contexts.")
        results = []

    if not results:
        try:
            recent_res = (
                supabase.table("emails")
                .select("id,subject,snippet,sender_email,sender_name,date,body_text")
                .eq("user_id", user_id)
                .order("date", desc=True)
                .limit(250)
                .execute()
            )
            query_lower = query.lower()
            candidates = recent_res.data or []
            matched = [
                email
                for email in candidates
                if query_lower in " ".join(
                    str(email.get(field) or "")
                    for field in ("subject", "snippet", "sender_email", "sender_name", "body_text")
                ).lower()
            ]
            results = (matched or candidates)[:top_k]
        except Exception as e:
            print(f"[Search Fallback Error] {e}")
            results = []

    # Format documents for Groq
    context_docs = []
    sources = []
    
    for i, doc in enumerate(results):
        context_docs.append(f"Email [{i+1}] Date: {doc.get('date')} | From: {doc.get('sender_name')} <{doc.get('sender_email')}>\nSubject: {doc.get('subject')}\nSnippet: {doc.get('snippet')}")
        
        sources.append({
            "id": doc.get('id'),
            "subject": doc.get('subject') or "No Subject",
            "sender_email": doc.get('sender_email', "unknown@example.com"),
            "sender_name": doc.get('sender_name', ""),
            "snippet": doc.get('snippet', ""),
            "date": str(doc.get('date')),
            "labels": [],
            "relevance_score": doc.get('similarity', 0)
        })

    context_str = "\n\n".join(context_docs)
    
    # 3. Call Groq for Context-Aware Generation
    system_prompt = (
        "You are MailLens, an expert AI email assistant. Output a highly professional, concise, and helpful response "
        "synthesized DIRECTLY from the provided email context. If you cannot answer the query using the context, explicitly say so. "
        "Do not hallucinate external details."
    )
    
    user_prompt = f"Context:\n{context_str}\n\nUser Query: {query}"
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_SEARCH_MODEL,
            temperature=0.2,
            max_tokens=600
        )
        answer = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"[Groq Error] LLM generation failed: {e}")
        answer = "Sorry, the AI inference model is currently unreachable or misconfigured."
        
    query_time_ms = int((time.time() - start_time) * 1000)
    
    return {
        "answer": answer,
        "sources": sources,
        "query_time_ms": query_time_ms
    }
