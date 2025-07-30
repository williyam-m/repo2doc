from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatMessageSerializer
from django.conf import settings
from ai_model.views import generate_ai_response

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
                
                # Generate AI response using the language model
                ai_response = generate_ai_response(prompt, max_tokens=settings.MAX_TOKENS)
                
            except Exception as e:
                # Fallback response if AI service fails
                ai_response = f"I'm sorry, I couldn't process your request. Error: {str(e)}"
            
            return Response({
                'response': ai_response
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
