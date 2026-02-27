import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

DB_PATH = "db"

# Load embeddings and vector DB
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectordb = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)

# Load LLM
llm = OllamaLLM(
    model="llama3.2:1b",
    temperature=0,
    num_ctx=2048
)

chat_history = []
response_cache = {}


def build_prompt(query: str, context: str, history_str: str) -> str:
    return f"""You are a helpful news assistant. Always respond in English only.
Use ONLY the document context below to answer...

### CHAT HISTORY:
{history_str}

### DOCUMENT CONTEXT:
{context}

### QUESTION:
{query}

### ANSWER:"""


def chatbot_ask(query: str) -> str:
    """
    Takes a user query, retrieves relevant news chunks from Chroma,
    and returns an LLM-generated answer grounded in the retrieved context.
    """
    global chat_history, response_cache

    query = query.strip()
    if not query:
        return "Please enter a valid question."

    # Return cached response if available
    if query in response_cache:
        print("(from cache)")
        return response_cache[query]

    # Retrieve relevant chunks
    results = vectordb.similarity_search(query, k=3)

    if not results:
        return "No relevant articles found in the knowledge base. Try running ingest.py first."

    context = "\n\n".join([doc.page_content for doc in results])[:3000]

    # Show sources to user
    sources = list({doc.metadata.get("source", "Unknown") for doc in results})
    sources_str = ", ".join(sources)

    # Build recent chat history string (last 4 messages = 2 turns)
    history_str = "\n".join(chat_history[-4:]) if chat_history else "None"

    prompt = build_prompt(query, context, history_str)

    try:
        response = llm.invoke(prompt)
    except Exception as e:
        return f"LLM error: {e}"

    # Cache and update history
    response_cache[query] = response
    chat_history.append(f"Human: {query}")
    chat_history.append(f"AI: {response}")

    return f"{response}\n\n📰 Sources: {sources_str}"


def clear_history():
    """Clear chat history and response cache."""
    global chat_history, response_cache
    chat_history = []
    response_cache = {}
    print("✅ Chat history and cache cleared.")


if __name__ == "__main__":
    print("🤖 News RAG Chatbot (type 'exit' to quit, 'clear' to reset history)")
    while True:
        q = input("\nYou: ").strip()
        if not q:
            continue
        if q.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        if q.lower() == "clear":
            clear_history()
            continue
        print("\nAI:", chatbot_ask(q))