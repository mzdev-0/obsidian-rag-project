"""
Configuration management for the RAG Micro-Agent.
Handles environment variables, provider selection, and fallback chains.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Try to import Langchain embeddings, with fallback
logger = logging.getLogger(__name__)

# Embedding model import with graceful fallback
try:
    from langchain_community.embeddings import LlamaCppEmbeddings
except ImportError:
    LlamaCppEmbeddings = None


@dataclass
class LLMConfig:
    """Configuration for LLM providers and models."""
    
    # Provider configuration
    use_online_llm: bool = True
    openrouter_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:latest"
    
    # Embedding configuration
    embedding_model_path: Optional[str] = None
    use_local_embeddings: bool = True
    
    # ChromaDB configuration
    db_path: str = "./data/chroma_db"
    collection_name: str = "obsidian_notes"
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables with fallbacks."""
        
        # Environment variable mapping
        config = cls()
        
        # LLM Provider settings
        config.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        config.use_online_llm = bool(config.openrouter_api_key) and os.getenv("USE_ONLINE_LLM", "true").lower() != "false"
        
        # Ollama settings
        config.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        config.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        
        # Embedding settings
        config.embedding_model_path = os.getenv("MODEL_PATH")
        config.use_local_embeddings = os.getenv("USE_LOCAL_EMBEDDINGS", "true").lower() != "false"
        
        # Database settings
        config.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        config.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "obsidian_notes")
        
        logger.info(f"Loaded config: use_online_llm={config.use_online_llm}, "
                   f"embedding_model={config.embedding_model_path or 'default'}, "
                   f"db_path={config.db_path}")
        
        return config


def get_embedding_function():
    """
    Get the configured embedding function based on environment settings.
    Returns LlamaCppEmbeddings instance or raises RuntimeError if unavailable.
    """
    if LlamaCppEmbeddings is None:
        raise RuntimeError("LlamaCppEmbeddings not available - install langchain-community")
    
    config = LLMConfig.from_env()
    
    if not config.use_local_embeddings:
        raise RuntimeError("Local embeddings disabled")
    
    model_path = config.embedding_model_path or os.path.join(
        os.path.dirname(__file__), "data", "models", "Qwen3-Embedding-0.6B-f16.gguf"
    )
    
    # Validate model file exists
    if not os.path.exists(model_path):
        raise RuntimeError(f"Embedding model not found at: {model_path}")
    
    return LlamaCppEmbeddings(
        model_path=model_path,
        n_gpu_layers=-1,
        n_batch=512,
        n_ctx=32768,
        verbose=False,
    )


def validate_config(config: LLMConfig) -> Dict[str, Any]:
    """Validate configuration and return status report."""
    
    issues = []
    warnings = []
    
    # Validate primary LLM configuration
    if config.use_online_llm:
        if not config.openrouter_api_key:
            issues.append("OPENROUTER_API_KEY environment variable is required when USE_ONLINE_LLM=true")
    else:
        # Test Ollama connectivity
        try:
            import requests
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                warnings.append(f"Ollama endpoint not responding at {config.ollama_base_url}")
            else:
                # Check if model exists
                models = response.json().get("models", [])
                if not any(m.get("name") == config.ollama_model for m in models):
                    warnings.append(f"Ollama model '{config.ollama_model}' not found locally")
        except Exception as e:
            warnings.append(f"Cannot connect to Ollama: {e}")
    
    # Validate embedding configuration
    if config.use_local_embeddings and not config.embedding_model_path:
        warnings.append("Using default embedding model - consider setting MODEL_PATH for specific model")
    
    if config.embedding_model_path and not os.path.exists(config.embedding_model_path):
        warnings.append(f"Embedding model file not found: {config.embedding_model_path}")
    
    # Validate database paths
    os.makedirs(config.db_path, exist_ok=True)
    
    return {
        "issues": issues,
        "warnings": warnings,
        "can_proceed": len(issues) == 0
    }