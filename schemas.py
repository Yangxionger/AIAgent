from typing import Any, Literal
from pydantic import BaseModel


# 前端 POST /ask 时发来的数据
class ChatRequest(BaseModel):
    question: str


# 图表配置
class ChartConfig(BaseModel):
    type: Literal["bar", "line", "none"]
    x_field: str | None = None
    y_field: str | None = None
    title: str | None = None


# LLM generate_analysis() 应该返回的数据结构
class AnalysisOutput(BaseModel):
    answer: str
    chart: ChartConfig


# FastAPI /ask 最终返回给前端的数据
class AskResponse(BaseModel):
    sql: str
    result: Any
    answer: str
    chart: ChartConfig | None = None