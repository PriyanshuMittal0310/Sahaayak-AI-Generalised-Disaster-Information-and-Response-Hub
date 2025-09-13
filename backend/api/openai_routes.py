from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import openai
from dotenv import load_dotenv
import os

router = APIRouter(prefix="/api/openai", tags=["openai"])

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

class PromptRequest(BaseModel):
    prompt: str

@router.post("/polish_alert")
async def polish_alert(request: Request, prompt: PromptRequest):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt.prompt}],
        max_tokens=180
    )
    polished = response.choices[0].message['content']
    return JSONResponse(content={"text": polished})

@router.post("/translate_alert")
async def translate_alert(request: Request, prompt: PromptRequest):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Translate the following to Hindi (<=180 chars, no PII)."},
            {"role": "user", "content": prompt.prompt}
        ],
        max_tokens=180
    )
    hindi = response.choices[0].message['content']
    return JSONResponse(content={"text": hindi})
