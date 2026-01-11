import sys
from pathlib import Path
from typing import Optional, Dict
import uuid

# Add project root to path for direct script execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.agent.orchestrator import handle_query


def process_chat(
    query: str,
    session_id: Optional[str] = None
) -> Dict:
    """
    Handles chat request logic:
    - Creates session_id if missing
    - Calls orchestrator
    - Returns unified response
    """

    # Backend owns session creation
    session_id = session_id or str(uuid.uuid4())

    result = handle_query(
        query=query,
        session_id=session_id
    )

    return {
        "answer": result["answer"],
        "source": result["source"],
        "session_id": session_id
    }
