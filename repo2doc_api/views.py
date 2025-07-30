from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import traceback
from django.conf import settings
from message_resource.ai_model_config import AI_PROMPT
from message_resource.api_message_resource import *
from ai_model.views import generate_ai_response

class GenerateDocView(APIView):
    def post(self, request):
        code = request.data.get(API_KEY_NAME.CODE)
        if not code:
            return Response({API_KEY_NAME.ERROR: ErrorMessages.MISSING_CODE}, status=status.HTTP_400_BAD_REQUEST)

        # Build the prompt with the code
        prompt = AI_PROMPT.getPromptForGenerateDoc(code)

        try:
            # Generate AI response using the language model
            result = generate_ai_response(prompt, max_tokens=settings.MAX_TOKENS)
            
            return Response({
                API_KEY_NAME.MESSAGE: SuccessMessages.DOCUMENTATION_GENERATED,
                API_KEY_NAME.DOCUMENTATION: result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            print(e)
            return Response({
                API_KEY_NAME.ERROR: str(e) or ErrorMessages.INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
