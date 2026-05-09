import os

from dotenv import load_dotenv

from openai import OpenAI
from openai import APIConnectionError
from openai import APIStatusError

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

    try:

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
            max_tokens=256,
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

    except APIConnectionError:

        yield (
            "⚠️ Unable to connect to the vLLM backend.\n\n"
            "Possible reasons:\n"
            "- backend container crashed\n"
            "- model still loading\n"
            "- GPU unavailable\n"
            "- Docker network issue\n\n"
            "Please check backend logs."
        )

    except APIStatusError as e:

        yield (
            f"Backend API error:\n\n"
            f"{str(e)}"
        )

    except Exception as e:

        yield (
            f"Unexpected error:\n\n"
            f"{str(e)}"
        )