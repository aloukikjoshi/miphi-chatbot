import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct")

client = OpenAI(
    base_url=VLLM_BASE_URL,
    api_key="EMPTY"
)


def generate_answer(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=VLLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=256,
    )
    return response.choices[0].message.content.strip()