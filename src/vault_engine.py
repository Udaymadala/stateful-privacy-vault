import uuid
import json
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

class StatefulTokenVault:
    def __init__(self, config_path: str = "config/vault_policy.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        self.analyzer = AnalyzerEngine()
        self.token_prefix = self.config.get("token_prefix", "TOKEN")
        self.token_entities = self.config.get("token_entities", [])
        
        # 🔒 Hardened Local Storage: The Token Vault
        # Maps: Token String -> Real Sensitive String
        self.vault = {}
        
        # Inject our explicit SSN pattern matcher from project 1
        ssn_pattern = Pattern(name="ssn_regex", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=1.0)
        custom_ssn_recognizer = PatternRecognizer(
            supported_entity="US_SSN", 
            patterns=[ssn_pattern],
            context=["ssn", "social", "security", "usssn"]
        )
        self.analyzer.registry.add_recognizer(custom_ssn_recognizer)

    def tokenize_text(self, text: str) -> str:
        """Finds sensitive data, stores it in the vault, and returns placeholder tokens."""
        if not text:
            return text
            
        # 1. Detect target entities based on our JSON policy rules
        analysis_results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.token_entities
        )
        
        # Sort results backwards by text placement so replacing strings doesn't mess up indexing positions
        sorted_results = sorted(analysis_results, key=lambda x: x.start, reverse=True)
        
        sanitized_text = text
        
        # 2. Extract real data, generate tokens, and populate our database vault map
        for result in sorted_results:
            real_value = text[result.start:result.end]
            entity_type = result.entity_type
            
            # Check if we already vaulted this specific text to keep tokens consistent
            existing_token = None
            for token, saved_value in self.vault.items():
                if saved_value == real_value:
                    existing_token = token
                    break
            
            if existing_token:
                current_token = existing_token
            else:
                # Generate a unique, unpredictable short token ID
                unique_id = str(uuid.uuid4())[:6].upper()
                current_token = f"[{self.token_prefix}_{entity_type}_{unique_id}]"
                
                # Lock it inside our local vault map
                self.vault[current_token] = real_value
            
            # Swap real data out for our trackable token placeholder
            sanitized_text = sanitized_text[:result.start] + current_token + sanitized_text[result.end:]
            
        return sanitized_text

    def detokenize_text(self, tokenized_text: str) -> str:
        """Scans text coming back from an AI model, locates tokens, and returns real data."""
        if not tokenized_text:
            return tokenized_text
            
        restored_text = tokenized_text
        
        # Search the text for any tokens registered in our storage pool and reverse them
        for token, original_value in self.vault.items():
            if token in restored_text:
                restored_text = restored_text.replace(token, original_value)
                
        return restored_text

# Quick Local Verification Block
if __name__ == "__main__":
    vault_agent = StatefulTokenVault()
    
    # Simulating a clinical scheduler input string
    incoming_prompt = "Schedule appointment for John Doe, phone 904-555-1234, SSN 000-11-2222 at the Downtown Clinic."
    print(f"1. Raw Inbound Message:\n   {incoming_prompt}\n")
    
    # Transform it to transit format
    safe_transit_payload = vault_agent.tokenize_text(incoming_prompt)
    print(f"2. Sanitized Payload Sent to External AI:\n   {safe_transit_payload}\n")
    
    print(f"🔒 Current Vault Registry Contents:")
    print(json.dumps(vault_agent.vault, indent=2))
    print("")
    
    # Simulating the AI processing the response and keeping the token placeholders intact
    simulated_ai_response = "SUCCESS: Appointment created for [VAULT_TOKEN_PERSON_XXXXXX] ([VAULT_TOKEN_PHONE_NUMBER_XXXXXX]) at the Downtown Clinic on Tuesday at 3pm."
    # Realistically, the AI will echo back the tokens it was handed, so let's simulate that matching exactly:
    active_tokens = list(vault_agent.vault.keys())
    for token in active_tokens:
        if "_PERSON_" in token:
            simulated_ai_response = simulated_ai_response.replace("[VAULT_TOKEN_PERSON_XXXXXX]", token)
        if "_PHONE_NUMBER_" in token:
            simulated_ai_response = simulated_ai_response.replace("[VAULT_TOKEN_PHONE_NUMBER_XXXXXX]", token)

    print(f"3. Raw Server Response Received From AI:\n   {simulated_ai_response}\n")
    
    # De-tokenize back to home system format
    final_internal_output = vault_agent.detokenize_text(simulated_ai_response)
    print(f"4. Re-identified Output Sent to Internal Clinic CRM:\n   {final_internal_output}")