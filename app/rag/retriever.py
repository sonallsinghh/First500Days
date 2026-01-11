import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "faiss_index/index.faiss"
META_PATH = "faiss_index/meta.pkl"

# Load embedding model once
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Load FAISS index
index = faiss.read_index(INDEX_PATH)

# Load metadata
with open(META_PATH, "rb") as f:
    metadata = pickle.load(f)


def retrieve_documents(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.05
):
    """
    Retrieve documents using semantic similarity search.
    
    Uses FAISS with sentence transformers embeddings to find semantically
    similar chunks based on meaning, not just keyword matching.
    """
    # Encode query into embedding vector
    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Search FAISS index for similar embeddings
    distances, indices = index.search(query_embedding, top_k)

    results = []
    sources = set()

    # Return results based on semantic similarity scores
    for score, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        # Filter by similarity threshold
        if score < similarity_threshold:
            continue

        doc = metadata[idx]
        results.append(doc["content"])
        sources.add(doc["source"])

    return results, list(sources)



if __name__ == "__main__":
    chunks, sources = retrieve_documents(
        "can we take emergency leave?"
    )

    print("Chunks:")
    for i, c in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ({len(c)} chars) ---")
        print(c)
        print()

    print("Sources:", sources)
