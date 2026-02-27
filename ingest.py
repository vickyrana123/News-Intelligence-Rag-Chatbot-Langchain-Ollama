import os
import requests
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()

DB_PATH = "db"
API_KEY = os.getenv("NEWS_API_KEY")


def ingest_documents(query: str = "tesla"):
    """Fetch news articles from NewsAPI, chunk, embed, and store in Chroma vector DB."""

    if not API_KEY:
        raise ValueError("NEWS_API_KEY not found. Please set it in your .env file.")

    print(f"Fetching news articles for query: '{query}'...")

    url = (
    "https://newsapi.org/v2/everything?"
    f"q={query}&"
    "language=en&"
    "sortBy=publishedAt&"
    f"apiKey={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("Request timed out. Please check your internet connection.")
        return
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return

    data = response.json()
    articles = data.get("articles", [])

    if not articles:
        print("No articles found.")
        return

    documents = []

    for article in articles:
        title = article.get("title") or ""
        description = article.get("description") or ""
        content = article.get("content") or ""
        source = article.get("source", {}).get("name") or ""
        published_at = article.get("publishedAt") or ""

        # Skip articles with no useful content
        if not title and not content:
            continue

        text = (
            f"Source: {source}\n"
            f"Published At: {published_at}\n"
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Content: {content}"
        )

        documents.append(Document(page_content=text, metadata={
            "source": source,
            "published_at": published_at,
            "title": title,
        }))

    print(f"Loaded {len(documents)} articles")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    vectordb.persist()
    print("✅ News knowledge base created successfully")


if __name__ == "__main__":
    ingest_documents()