from rest_framework import serializers

class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    file_content = serializers.CharField(required=True)
    file_name = serializers.CharField(required=True)