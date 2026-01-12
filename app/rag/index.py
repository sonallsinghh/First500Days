import faiss
import pickle
from app.rag.ingest import load_documents
from app.rag.hf_embeddings import get_embeddings

INDEX_PATH = "faiss_index/index.faiss"
META_PATH = "faiss_index/meta.pkl"


def build_index(doc_dir: str):
    documents = load_documents(doc_dir)
    texts = [doc["content"] for doc in documents]

    # 🔹 Get embeddings from Hugging Face API (normalized for cosine similarity)
    print(f"Generating embeddings for {len(texts)} chunks using Hugging Face API...")
    embeddings = get_embeddings(texts, normalize=True, batch_size=32)

    dimension = embeddings.shape[1]

    # 🔹 Use Inner Product for cosine similarity
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Persist index
    faiss.write_index(index, INDEX_PATH)

    # Persist metadata
    with open(META_PATH, "wb") as f:
        pickle.dump(documents, f)

    print(f"FAISS index built with {len(documents)} chunks")
