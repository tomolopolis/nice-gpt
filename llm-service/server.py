
from fastapi import FastAPI
from pydantic import BaseModel

from medchain.start_llm import load_llm

app = FastAPI()

qa_sys = load_llm()


class DocSource(BaseModel):
    source: str
    content: str


class Query(BaseModel):
    query_str: str


class QueryResp(BaseModel):
    answer: str
    sources: list[DocSource]


class PromptResponse(BaseModel):
    prompt: str


@app.get("/")
async def root():
    return {
        "message": "LLM Server root",
    #     "qa_sys": "... what qa_sys is running ... ",
    }


@app.post("/qa/")
async def qa(query: Query) -> QueryResp:
    answer, sources = qa_sys.prompt_once(query.query_str)
    return QueryResp(
        answer=answer,
        sources=[DocSource(source=s.metadata['source'], content=s.page_content) for s in sources]
    )


@app.post("/gen-prompt/")
async def gen_prompt(query: Query) -> PromptResponse:
    return PromptResponse(prompt=qa_sys.formatted_prompt(query.query_str))
