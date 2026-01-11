import faiss
import pickle
from sentence_transformers import SentenceTransformer
from app.rag.ingest import load_documents

INDEX_PATH = "faiss_index/index.faiss"
META_PATH = "faiss_index/meta.pkl"

# Load embedding model ONCE
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def build_index(doc_dir: str):
    documents = load_documents(doc_dir)
    texts = [doc["content"] for doc in documents]

    # 🔹 Normalize embeddings for cosine similarity
    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

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
