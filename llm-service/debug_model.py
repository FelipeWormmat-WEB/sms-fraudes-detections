import sys
import os
from pathlib import Path

def debug_model():
    model_path = Path("/app/models/tinyllama-1.1b-chat-v0.3")
    
    print("=== DEBUG DO MODELO ===")
    print(f"Python path: {sys.path}")
    print(f"Model path exists: {model_path.exists()}")
    
    if model_path.exists():
        print("Files in model directory:")
        for f in model_path.iterdir():
            print(f"  - {f.name}")
    
    # Testar importações
    try:
        from transformers import __version__ as tf_version
        print(f"Transformers version: {tf_version}")
    except ImportError as e:
        print(f"Transformers import error: {e}")
    
    try:
        import sentencepiece as sp
        print(f"SentencePiece version: {sp.__version__}")
    except ImportError as e:
        print(f"SentencePiece import error: {e}")

if __name__ == "__main__":
    debug_model()