import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIConnectionError
from openai import APIStatusError

load_dotenv()

VLLM_BASE_URL = os.getenv(
    "VLLM_BASE_URL",
    "http://host.docker.internal:8000/v1"
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
    system_prompt: str,
    user_prompt: str
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
                },
            ],
            temperature=0.2,
            stream=True,
        )

        for chunk in stream:

            if chunk.choices:

                delta = chunk.choices[0].delta.content

                if delta:
                    yield delta

    except APIConnectionError:

        yield (
            "⚠️ Unable to connect to the local vLLM backend.\n\n"
            "Possible reasons:\n"
            "- vLLM container is still starting\n"
            "- model is loading into memory\n"
            "- backend service is not running\n"
            "- incorrect VLLM_BASE_URL\n\n"
            "Please wait a moment and try again."
        )

    except APIStatusError as e:

        yield (
            f"⚠️ Backend API error occurred.\n\n"
            f"Status Code: {e.status_code}\n"
            f"Message: {str(e)}"
        )

    except Exception as e:

        yield (
            f"⚠️ Unexpected error occurred:\n\n"
            f"{str(e)}"
        )