from django.conf import settings
import requests
import json
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from llama_cpp import Llama


logger = logging.getLogger(__name__)

llm = Llama(model_path=settings.LLAMA_CPP_PATH, n_ctx=4096)


def generate_ai_response(prompt, max_tokens):
    """
    Generates a response from the AI language model using the provided prompt.
    
    This function uses llama-cpp-python to directly interact with the Llama model.
    
    Args:
        prompt (str): The input prompt for the language model
        max_tokens (int): Maximum number of tokens to generate in response
        
    Returns:
        str: The generated text response from the language model
    """
    try:
        output = llm(prompt, max_tokens=max_tokens, stop=["</s>"])
        
        # Extract text from output
        generated_text = output["choices"][0]["text"]
        
        logger.info(f"Generated response of length: {len(generated_text)} characters")
        return generated_text
    except Exception as e:
        print(e)
        logger.error(f"Error in LLM processing: {str(e)}")
        return "I encountered an error processing your request. Please try again later."

@api_view(['POST'])
def ai_model_api(request):
    """
    API endpoint for processing AI requests
    
    Expects a JSON payload with:
    - prompt: The text prompt to process
    - max_tokens: (Optional) Maximum tokens to generate
    
    Returns:
    - response: The generated AI response
    """
    prompt = request.data.get('prompt')
    max_tokens = request.data.get('max_tokens', settings.MAX_TOKENS)
    
    if not prompt:
        return Response(
            {"error": "Missing required parameter: prompt"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    response_text = generate_ai_response(prompt, max_tokens)
    
    return Response({"response": response_text})
