from django.conf import settings

class AI_PROMPT:
    @staticmethod
    def getPromptForGenerateDoc(code):
        return f"Generate clear and helpful documentation for the following code:\n\n{code}"


class ModelConfig:
    @staticmethod
    def isTransformerEnabled():
        return settings.AI_MODEL_DEPLOY_TYPE == "transformer"
    
    @staticmethod
    def isOllamaEnabled():
        return settings.AI_MODEL_DEPLOY_TYPE == "ollama"

    @staticmethod
    def isQwenFromTransformerEnabled():
        return settings.AI_MODEL == "qwen" and settings.AI_MODEL_DEPLOY_TYPE == "transformer"

    @staticmethod
    def isLlamaFromOllamaEnabled():
        return settings.AI_MODEL == "llama" and settings.AI_MODEL_DEPLOY_TYPE == "ollama"
