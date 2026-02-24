# harness/client.py

class LegacyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        print("LegacyClient initialized.")

    def generate(self, prompt: str):
        print(f"Legacy client generating for prompt: {prompt[:50]}...")
        # Mock response
        return '{"response": "This is a mock response from the legacy client."}'

