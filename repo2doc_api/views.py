from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests

from ai_model.services.qwen_model import load_qwen_model_from_transformer
from admin_console.utils import ModelConfig

class GenerateDocView(APIView):
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)

        prompt = f"Generate clear and helpful documentation for the following code:\n\n{code}"

        try:
            if ModelConfig.isQwenFromTransformerEnabled():
                generator = load_qwen_model_from_transformer()
                result = generator(prompt, max_new_tokens=300, do_sample=True)[0]['generated_text']
                return Response({'documentation': result})

            elif ModelConfig.isLlamaFromOllamaEnabled():
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama2:7b", "prompt": prompt, "stream": False}
                )
                result = response.json().get("response")
                return Response({'documentation': result})

            else:
                return Response({'error': 'No valid model configuration found'}, status=400)

        except Exception as e:
            return Response({'error': str(e)}, status=500)
