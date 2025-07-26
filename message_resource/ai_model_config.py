from django.conf import settings

class AI_PROMPT:
    @staticmethod
    def getPromptForGenerateDoc(code):
        return f"find below code lanugauge (only give one word of programing name) : {code}"
        #return f"You are an expert technical writer and software documentation specialist. Your task is to analyze the given code snippet and generate clean, professional, and developer-friendly documentation suitable for inclusion in a technical documentation site, internal wiki, or public API reference. The code can be of any type: utility function, API endpoint, data model, class, script, or module. Your documentation should be clear and concise, but also complete, providing just enough context and structure for a developer to understand, integrate, and use the code effectively without reading its full implementation. Generate clear and helpful documentation for the following code:\n\n{code}"


class ModelConfig:

    @staticmethod
    def isLlama_2_7b_ModelEnabled():
        return settings.AI_MODEL == "llama_2_7b"

    @staticmethod
    def isGeminiModelEnabled():
        return settings.AI_MODEL == "gemini"
   
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
