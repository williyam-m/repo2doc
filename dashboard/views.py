from django.shortcuts import render
import requests


def index(request):
    context = {}
    if request.method == 'POST':
        code_file = request.FILES.get('code_file')
        if code_file:
            code = code_file.read().decode('utf-8')
            response = requests.post(
                'http://localhost:8000/api/repo2doc/',
                json={"code": code}
            )
            if response.status_code == 200:
                context['documentation'] = response.json().get('documentation')
            else:
                context['error'] = response.json().get('detail', 'Something went wrong')
    return render(request, 'index.html', context)
