from django.conf import settings

class ModelConfig:
    
    @staticmethod
    def isQwenFromTransformerEnabled():
        return settings.AI_MODEL == "qwen" and settings.AI_MODEL_DEPLOY_TYPE == "transformer"

    @staticmethod
    def isLlamaFromOllamaEnabled():
        return settings.AI_MODEL == "llama" and settings.AI_MODEL_DEPLOY_TYPE == "ollama"
