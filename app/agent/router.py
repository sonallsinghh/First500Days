import sys
from pathlib import Path

# Add project root to path for direct script execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from openai import OpenAI
from app.agent.prompts import ROUTER_PROMPT
from app.config import OPENAI_API_KEY

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)


def route_query(query: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict classifier."},
                {
                    "role": "user",
                    "content": ROUTER_PROMPT.format(query=query)
                }
            ],
            temperature=0
        )

        decision = response.choices[0].message.content.strip().upper()

        if decision not in ["DIRECT", "RETRIEVE"]:
            return "RETRIEVE"  # safe default

        return decision
    except Exception as e:
        # Check if it's an authentication error
        error_str = str(e).lower()
        if "401" in error_str or "authentication" in error_str or "invalid_api_key" in error_str:
            raise ValueError(
                "Invalid OpenAI API key. Please check your .env file and ensure "
                "you have a valid API key from https://platform.openai.com/account/api-keys"
            ) from e
        raise


if __name__ == "__main__":
    print(route_query("Hello, how are you?"))
    print(route_query("What is the paternity leave policy?"))
