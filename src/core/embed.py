# --- File: embedder.py ---

# 1. Installation
# pip install langchain-community chromadb llama-cpp-python

from langchain_community.embeddings import LlamaCppEmbeddings
import os

# --- Configuration ---
# Ensure you have downloaded the GGUF model and placed it in a known directory.
# You can find it on Hugging Face Hub. For example:
# huggingface-cli download Qwen/Qwen2-7B-Instruct-GGUF qwen2-7b-instruct-q4_k_m.gguf --local-dir ./models
import os
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "models", "Qwen3-Embedding-0.6B-f16.gguf")  # Updated path for new structure

# --- Model Loading ---
# Initialize the LlamaCppEmbeddings model
# This gives you fine-grained control over the model's parameters.
# n_gpu_layers: Offload layers to GPU. -1 means all possible layers. Adjust if you have a GPU.
# n_batch: Number of tokens to process in parallel. Adjust based on your hardware.
# n_ctx: The context size for the model.
# verbose: Set to True for detailed logging.
try:
    llama_embedder = LlamaCppEmbeddings(  # pyright: ignore[reportCallIssue]
        model_path=MODEL_PATH,
        n_gpu_layers=-1,
        n_batch=512,
        n_ctx=32768,
        verbose=False,
    )
    print("✅ GGUF Embedding model loaded successfully.")
except Exception as e:
    print(e)
#    print(f"❌ Error loading model: {e}")
#    print("Please ensure the MODEL_PATH is correct and the GGUF file is not corrupted.")
#    exit()


# --- Custom Embedding Logic (from your PRD) ---


# This function prepares the text according to your clean embedding strategy
def create_embedding_text(title, heading, content):
    """
    Creates the clean content string for embedding.
    Format: "{note.title} | {section.heading}\n\n{section.content}"
    """
    return f"{title} | {heading}\n\n{content}"


# --- Example Usage ---

# Define some sample note sections based on your PRD's data structure
note_sections = [
    {
        "title": "Hybrid Retrieval Systems",
        "heading": "Two-Stage Retrieval",
        "content": "A hybrid retrieval system combines structured metadata for precise filtering and semantic search for content relevance. The key is to intersect the results to prevent false positives.",
    },
    {
        "title": "Embedding Strategies",
        "heading": "Clean Content Embedding",
        "content": "To improve search quality, it's crucial to embed only the clean semantic content. Metadata like dates and tags should be stored separately, not included in the text sent to the embedding model.",
    },
]

# Prepare the texts for embedding
texts_to_embed = [
    create_embedding_text(sec["title"], sec["heading"], sec["content"])
    for sec in note_sections
]

print("\n--- Texts to be Embedded ---")
for text in texts_to_embed:
    print(f'-> "{text[:80]}..."')

# Generate the embeddings
try:
    embeddings = llama_embedder.embed_documents(texts_to_embed)  # pyright: ignore
    print(f"\n✅ Successfully generated {len(embeddings)} embeddings.")
    print(f"   Each embedding has a dimension of: {len(embeddings[0])}")

    # You would now store these embeddings in ChromaDB, associated with your metadata.

except Exception as e:
    print(f"❌ Error during embedding generation: {e}")
