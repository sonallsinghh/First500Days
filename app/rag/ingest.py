from typing import List
from pathlib import Path
import tiktoken
from pypdf import PdfReader

# OpenAI-compatible tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")


# -------------------------
# Text Extraction
# -------------------------

def extract_text_from_txt(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)


# -------------------------
# Chunking
# -------------------------

def split_by_sections(text: str) -> List[str]:
    # Simple section split (can be improved later)
    return [section for section in text.split("\n\n") if section.strip()]


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
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


# -------------------------
# Document Loader
# -------------------------

def load_documents(doc_dir: str):
    documents = []

    for file in Path(doc_dir).iterdir():
        if file.suffix.lower() == ".txt":
            raw_text = extract_text_from_txt(file)

        elif file.suffix.lower() == ".pdf":
            raw_text = extract_text_from_pdf(file)

        else:
            continue  # unsupported file type

        sections = split_by_sections(raw_text)

        for section in sections:
            chunks = chunk_text(section)

            for chunk in chunks:
                documents.append({
                    "content": chunk,
                    "source": file.name
                })

    return documents
