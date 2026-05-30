import os

class LLMconfig:
    def __init__(self):
        self.key = os.environ.get("LLM_API_KEY")
        self.base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        self.model =  os.environ.get("LLM_MODEL", "deepseek/deepseek-v4-pro")