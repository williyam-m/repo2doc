from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatMessageSerializer
import os
import google.generativeai as genai
from django.conf import settings

class ChatAPIView(APIView):
    """
    API endpoint for chat interactions with the AI model about code files.
    """
    def post(self, request, format=None):
        serializer = ChatMessageSerializer(data=request.data)
        
        if serializer.is_valid():
            message = serializer.validated_data['message']
            file_content = serializer.validated_data['file_content']
            file_name = serializer.validated_data['file_name']
            
            try:
                # Configure Google GenerativeAI with API key from settings
                api_key = getattr(settings, 'GENAI_API_KEY', None)
                if api_key:
                    genai.configure(api_key=api_key)
                    
                    # Configure the model
                    generation_config = {
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                    }
                    
                    # Get a model
                    model = genai.GenerativeModel(
                        model_name="gemini-pro",
                        generation_config=generation_config
                    )
                    
                    # Create prompt with context
                    prompt = f"""
                    I'm looking at this file: {file_name}
                    
                    Here's the content:
                    ```
                    {file_content}
                    ```
                    
                    My question is: {message}
                    
                    Please provide a detailed and helpful response focused specifically on this code.
                    """
                    
                    # Generate response
                    response = model.generate_content(prompt)
                    ai_response = response.text
                    
                else:
                    # Fallback response in case of any error
                    ai_response = f"I'm sorry, I couldn't process your request. Error: {str(e)}"
            except Exception as e:
                # Fallback response if Google AI is not configured
                ai_response = "I'm sorry, I couldn't process your request. The AI service is not properly configured."
            
            return Response({
                'response': ai_response
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
