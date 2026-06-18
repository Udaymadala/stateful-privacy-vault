# Stateful HIPAA Tokenization Vault API (v2.0.0)

An enterprise-grade, zero-trust data privacy gateway designed to securely bridge regulated healthcare systems with external Large Language Models (LLMs). 

Unlike traditional destructive redaction engines, this gateway operates as a stateful, bidirectional middleware proxy utilizing a secure local Token Vault pattern.

### 🧠 Core Architecture Flow
1. **Inbound Tokenization (`POST /v2/tokenize`):** Intercepts raw text inputs locally. Utilizes an NLP processing pipeline augmented with custom regex pattern recognizers to isolate high-risk entities (Names, Phones, SSNs, Locations) and swaps them with randomized alphanumeric tokens.
2. **Secure AI Transit:** Sends completely anonymized text to downstream AI models, retaining 100% of the operational business context without exposing real identities.
3. **Outbound Detokenization (`POST /v2/detokenize`):** Intercepts the incoming model response stream, matches the unique token keys against the isolated local database registry, and dynamically reconstructs the real data attributes before patching back into the internal CRM/Database.

### 🛠️ Tech Stack
* **Framework:** FastAPI, Uvicorn (Asynchronous Python Web Server)
* **NLP Pipeline:** Microsoft Presidio Analyzer Engine, spaCy (`en_core_web_lg`)
* **Policy Management:** Decoupled JSON-based compliance controls (`vault_policy.json`)
