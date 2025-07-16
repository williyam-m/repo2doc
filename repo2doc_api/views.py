from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings

from ai_model.services.qwen_model import load_qwen_model_from_transformer
from admin_console.ai_model_config import *
from admin_console.api_message_resource import *

class GenerateDocView(APIView):

    def post(self, request):
        print("1")
        code = request.data.get(API_KEY_NAME.CODE)
        if not code:
            return Response({API_KEY_NAME.ERROR: ErrorMessages.MISSING_CODE}, status=status.HTTP_400_BAD_REQUEST)

        prompt = AI_PROMPT.getPromptForGenerateDoc(code)

        try:
            if ModelConfig.isOllamaEnabled():

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
                return Response({
                    API_KEY_NAME.MESSAGE: SuccessMessages.DOCUMENTATION_GENERATED,
                    API_KEY_NAME.DOCUMENTATION: result
                }, status=status.HTTP_200_OK)

            elif ModelConfig.isTransformerEnabled():

                generator = load_qwen_model_from_transformer()
                result = generator(prompt, max_new_tokens=settings.MAX_TOKENS, do_sample=True)[0]['generated_text']
                return Response({
                    API_KEY_NAME.MESSAGE: SuccessMessages.DOCUMENTATION_GENERATED,
                    API_KEY_NAME.DOCUMENTATION: result
                }, status=status.HTTP_200_OK)


            else:
                return Response({API_KEY_NAME.ERROR: ErrorMessages.INVALID_MODEL_CONFIG}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({API_KEY_NAME.ERROR: str(e) or ErrorMessages.INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
