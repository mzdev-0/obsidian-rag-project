import logging
from typing import List
from langchain.embeddings.base import Embeddings
from langchain_core.documents import Document
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from llama_cpp import Llama

# --- 1. Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 2. LlamaCppEmbeddings Class (as created before)---
class LlamaCppEmbeddings(Embeddings):
    """
    LangChain embeddings integration for llama-cpp-python.
    """

    def __init__(self, model_path: str, **kwargs):
        try:
            self.model = Llama(model_path=model_path, embedding=True, **kwargs)
        except Exception as e:
            logger.error(f"Error initializing Llama model: {e}")
            raise

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        result = self.model.create_embedding(texts)
        if "data" not in result or not isinstance(result["data"], list):
            logger.error(f"Unexpected output format from create_embedding: {result}")
            return []
        return [item["embedding"] for item in result["data"] if "embedding" in item]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]


# --- 3. Placeholder LLM for the RAG Chain ---
class PlaceholderLLM(LLM):
    """A placeholder LLM for demonstration purposes."""

    def _call(self, prompt: str, stop: List[str] = None) -> str:
        return "This is a placeholder response. In a real application, you would use a proper LLM to answer based on the context."

    @property
    def _llm_type(self) -> str:
        return "placeholder"


# --- 4. Main Example ---
if __name__ == "__main__":
    # --- Configuration ---
    MODEL_PATH = "./models/Qwen3-Embedding-8B-Q4_K_M.gguf"
    # Optional: Add GPU acceleration parameters if needed
    MODEL_KWARGS = {
        # "n_gpu_layers": -1,
        # "n_ctx": 2048,
    }

    try:
        # --- Initialize the Embedding Model ---
        logger.info(f"Loading embedding model from: {MODEL_PATH}")
        embeddings = LlamaCppEmbeddings(model_path=MODEL_PATH, **MODEL_KWARGS)
        logger.info("Embedding model loaded successfully.")

        # --- Create a ChromaDB Vector Store ---
        logger.info("Creating ChromaDB vector store...")

        # Sample documents to be added to the vector store
        texts = [
            "The Eiffel Tower, located in Paris, France, was completed in 1889.",
            "The Great Wall of China is a series of fortifications made of stone, brick, tamped earth, wood, and other materials.",
            "The Colosseum in Rome, Italy, is an oval amphitheatre in the centre of the city.",
            "The official currency of Japan is the Yen.",
            "The Amazon rainforest is the largest tropical rainforest in the world.",
        ]
        documents = [Document(page_content=text) for text in texts]

        # Create the Chroma vector store from the documents
        # This will automatically embed the documents and store them.
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            # You can persist the database to disk by specifying a directory
            # persist_directory="./chroma_db"
        )
        logger.info("ChromaDB vector store created and documents embedded.")

        # --- Perform a Similarity Search ---
        query = "What is a famous landmark in France?"
        logger.info(f"\nPerforming similarity search for query: '{query}'")

        # `k` specifies the number of most similar documents to retrieve
        similar_docs = vector_store.similarity_search(query, k=2)

        logger.info("Found similar documents:")
        for doc in similar_docs:
            logger.info(f"- {doc.page_content}")

        # --- Use the Vector Store as a Retriever in a RAG Chain ---
        logger.info("\nSetting up a RetrievalQA chain...")

        # The retriever is responsible for fetching relevant documents
        retriever = vector_store.as_retriever()

        # The LLM is responsible for generating an answer based on the retrieved documents.
        # We use our placeholder LLM here. In a real-world scenario, you would
        # initialize a proper LLM from LangChain (e.g., from llama-cpp-python, OpenAI, etc.)
        llm = PlaceholderLLM()

        # The prompt template ensures the LLM receives the context and question in a structured way.
        prompt_template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.

        {context}

        Question: {question}
        Helpful Answer:"""
        QA_PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        # Create the RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True,  # Optionally return the source documents
        )

        logger.info("RAG chain created. Now asking a question...")

        # Ask a question using the RAG chain
        rag_query = "What was built in Rome, Italy?"
        result = qa_chain({"query": rag_query})

        logger.info(f"\nQuery: {rag_query}")
        logger.info(f"Answer: {result['result']}")
        logger.info("Source Documents:")
        for doc in result["source_documents"]:
            logger.info(f"- {doc.page_content}")

    except Exception as e:
        logger.error(f"\nAn error occurred during the example: {e}")
        logger.error(
            "Please check the model path and ensure all dependencies are installed."
        )
