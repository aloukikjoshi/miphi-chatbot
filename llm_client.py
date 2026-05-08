import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

VLLM_BASE_URL = os.getenv(
    "VLLM_BASE_URL",
    "http://vllm:8000/v1"
)

VLLM_MODEL = os.getenv(
    "VLLM_MODEL",
    "meta-llama/Llama-3.2-1B-Instruct"
)

client = OpenAI(
    base_url=VLLM_BASE_URL,
    api_key="EMPTY"
)


def generate_answer_stream(
    system_prompt,
    user_prompt
):

    stream = client.chat.completions.create(
        model=VLLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.3,
        max_tokens=512,
        stream=True
    )

    for chunk in stream:

        if chunk.choices:

            delta = (
                chunk
                .choices[0]
                .delta.content
            )

            if delta:
                yield delta