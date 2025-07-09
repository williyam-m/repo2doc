from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch


tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen1.5-7B-Chat")
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen1.5-7B-Chat",
    device_map="auto",
    torch_dtype=torch.float16 
)


generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

class GenerateDocView(APIView):
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)

        prompt = f"Generate clear and helpful documentation for the following code:\n\n{code}"

        try:
            result = generator(prompt, max_new_tokens=300, do_sample=True)[0]['generated_text']
            return Response({'documentation': result})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
