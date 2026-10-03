from typing import Any,Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from generate_sql import ask_data_agent, generate_sql,generate_answer
from schemas import ChatRequest, AskResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ask",response_model=AskResponse)
def ask_with_sql(request:ChatRequest):
    sql,result,answer,chart=ask_data_agent(request.question)
    return {
        "sql": sql,
        "result": result,
        "answer": answer,
        "chart":chart
    }
