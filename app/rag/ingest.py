from typing import List
import tiktoken
from pathlib import Path

# Use OpenAI-compatible tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

def split_by_sections(text: str):
    sections = text.split("\n\n")
    return sections

def chunk_text(
    text: str,
    chunk_size: int = 250,
    overlap: int = 50
) -> List[str]:
    tokens = tokenizer.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

        start = end - overlap

    return chunks


def load_documents(doc_dir: str):
    documents = []

    for file in Path(doc_dir).glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            chunks = chunk_text(text)

            for chunk in chunks:
                documents.append({
                    "content": chunk,
                    "source": file.name
                })

    return documents

