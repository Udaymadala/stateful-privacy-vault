from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.vault_engine import StatefulTokenVault

app = FastAPI(
    title="Stateful HIPAA Tokenization Vault API",
    description="A secure gateway that dynamically tokenizes and detokenizes PHI to protect data in transit to AI models.",
    version="2.0.0"
)

# Initialize our stateful vault engine globally
vault = StatefulTokenVault()

# Define incoming request body structures
class TokenizeRequest(BaseModel):
    text: str

class DetokenizeRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {
        "gateway": "Stateful HIPAA Tokenization Vault",
        "status": "OPERATIONAL",
        "active_tokens_in_memory": len(vault.vault)
    }

@app.post("/v2/tokenize")
def tokenize_payload(payload: TokenizeRequest):
    try:
        tokenized_output = vault.tokenize_text(payload.text)
        return {
            "original_length": len(payload.text),
            "tokenized_text": tokenized_output,
            "status": "TRANSIT_SAFE"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v2/detokenize")
def detokenize_payload(payload: DetokenizeRequest):
    try:
        restored_output = vault.detokenize_text(payload.text)
        return {
            "tokenized_length": len(payload.text),
            "restored_text": restored_output,
            "status": "RE_IDENTIFIED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v2/vault/inspect")
def inspect_vault():
    """Secure endpoint to check the current token inventory mapping."""
    return {
        "total_active_mappings": len(vault.vault),
        "registry": vault.vault
    }