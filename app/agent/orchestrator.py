import sys
from pathlib import Path
from typing import Optional

# Add project root to path for direct script execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.agent.router import route_query
from app.agent.prompts import ANSWER_PROMPT
from app.rag.retriever import retrieve_documents
from app.agent.memory import get_memory, update_memory

client = OpenAI(api_key=OPENAI_API_KEY)


def handle_query(query: str, session_id: Optional[str] = None):
    """
    Orchestrates routing, retrieval (if needed), answer generation,
    and session-based memory.
    """

    decision = route_query(query)
    messages = []

    if session_id:
        messages.extend(get_memory(session_id))

    messages.append({"role": "user", "content": query})

    if decision == "DIRECT":
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )

        answer = response.choices[0].message.content.strip()

        if session_id:
            update_memory(session_id, "user", query)
            update_memory(session_id, "assistant", answer)

        return {
            "answer": answer,
            "source": []
        }

    chunks, sources = retrieve_documents(query)

    if not chunks:
        answer = "Information not found in provided documents."

        if session_id:
            update_memory(session_id, "user", query)
            update_memory(session_id, "assistant", answer)

        return {
            "answer": answer,
            "source": []
        }

    context = "\n\n".join(chunks)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You answer strictly using the provided context."
            },
            {
                "role": "user",
                "content": ANSWER_PROMPT.format(
                    context=context,
                    query=query
                )
            }
        ],
        temperature=0
    )

    answer = response.choices[0].message.content.strip()

    if session_id:
        update_memory(session_id, "user", query)
        update_memory(session_id, "assistant", answer)

    return {
        "answer": answer,
        "source": sources
    }

if __name__ == "__main__":
    sid = "test-session"

    print(handle_query("Hello, how are you?", sid))
    print(handle_query("What is the paternity leave policy?", sid))
    print(handle_query("Can it be carried forward?", sid))
