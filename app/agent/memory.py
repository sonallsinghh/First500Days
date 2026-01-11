from collections import defaultdict
from typing import List, Dict

# session_id -> list of messages
_session_memory: Dict[str, List[dict]] = defaultdict(list)

MAX_HISTORY = 6  # last 3 user + 3 assistant turns


def get_memory(session_id: str) -> List[dict]:
    return _session_memory.get(session_id, [])


def update_memory(session_id: str, role: str, content: str):
    _session_memory[session_id].append(
        {"role": role, "content": content}
    )

    # Sliding window
    if len(_session_memory[session_id]) > MAX_HISTORY:
        _session_memory[session_id] = _session_memory[session_id][-MAX_HISTORY:]
