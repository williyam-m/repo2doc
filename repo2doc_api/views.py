from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
import traceback
# Comment out the import to avoid the dependency error
# from llama_cpp import Llama
# import google.generativeai as genai


#from ai_transformer.services.qwen_model import load_qwen_model_from_transformer
from message_resource.ai_model_config import *
from message_resource.api_message_resource import *


# Comment out the llama initialization
# llm = Llama(model_path=settings.LLAMA_CPP_PATH)
# Comment out Gemini model configuration to avoid errors
# genai.configure(api_key=settings.GOOGLE_GENAI_API_KEY)
# model = genai.GenerativeModel(settings.AI_MODEL_NAME)


class GenerateDocView(APIView):

    def post(self, request):
        code = request.data.get(API_KEY_NAME.CODE)
        if not code:
            return Response({API_KEY_NAME.ERROR: ErrorMessages.MISSING_CODE}, status=status.HTTP_400_BAD_REQUEST)

        prompt = AI_PROMPT.getPromptForGenerateDoc(code)

        try:
            if ModelConfig.isGeminiModelEnabled():
                # Comment out Gemini model usage
                # response = model.generate_content(prompt)
                # result = response.text
                result = "This is a placeholder for Gemini model documentation."

            elif ModelConfig.isLlama_2_7b_ModelEnabled():
                # Comment out the Llama model usage to avoid errors
                # output = llm(prompt, max_tokens=settings.MAX_TOKENS, stop=["</s>"])
                # result = output["choices"][0]["text"]
                result = "This is a placeholder for Llama model documentation."


            elif ModelConfig.isOllamaEnabled():
                
                api_url = settings.OLLAMA_URL + "/api/generate"
                response = requests.post(
                    api_url,
                    json={
                        "model": settings.AI_MODEL_NAME,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": settings.TEMPARATURE,
                            "max_tokens": settings.MAX_TOKENS
                        }
                    }
                )
                result = response.json().get("response")

                '''
                elif ModelConfig.isTransformerEnabled():

                    generator = load_qwen_model_from_transformer()
                    result = generator(prompt, max_new_tokens=settings.MAX_TOKENS, do_sample=True)[0]['generated_text']
                '''


            else:
                return Response({API_KEY_NAME.ERROR: ErrorMessages.INVALID_MODEL_CONFIG}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                    API_KEY_NAME.MESSAGE: SuccessMessages.DOCUMENTATION_GENERATED,
                    API_KEY_NAME.DOCUMENTATION: result
                }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            print(e)
            return Response({API_KEY_NAME.ERROR: str(e) or ErrorMessages.INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
