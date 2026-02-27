from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from rag import chatbot_ask, clear_history
import uvicorn

app = FastAPI(
    title="News RAG Chatbot",
    description="A RAG-based chatbot powered by Ollama and NewsAPI",
    version="1.0.0"
)

# Allow frontend apps (Streamlit, React, etc.) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Question must not be empty.")
        return v.strip()


class ClearResponse(BaseModel):
    message: str


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "✅ News RAG Chatbot API is running"}


@app.post("/ask")
def ask(payload: Question):
    """Ask a question and get an answer grounded in news articles."""
    try:
        answer = chatbot_ask(payload.question)
        return {
            "question": payload.question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.post("/clear")
def clear():
    """Clear chat history and response cache."""
    try:
        clear_history()
        return {"message": "✅ Chat history and cache cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)