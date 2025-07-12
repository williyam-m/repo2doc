from django.shortcuts import render
from django.conf import settings
import requests
from admin_console.api_message_resource import *


def index(request):
    context = {}
    if request.method == 'POST':
        code_file = request.FILES.get('code_file')
        if code_file:
            code = code_file.read().decode('utf-8')
            api_url = settings.HOST_URL + "/api/repo2doc/"
            response = requests.post(
                api_url,
                json={API_KEY_NAME.CODE: code}
            )
            print(response.json())
            if response.status_code == 200:
                context[API_KEY_NAME.DOCUMENTATION] = response.json().get(API_KEY_NAME.DOCUMENTATION)
            else:
                context[API_KEY_NAME.ERROR] = response.json().get(API_KEY_NAME.DETAIL, ErrorMessages.INTERNAL_SERVER_ERROR)
    return render(request, 'index.html', context)
