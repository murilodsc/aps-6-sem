from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import base64
import json
from .models import FotoCapturada


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'index')
            messages.success(request, f'Bem-vindo(a), {user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Você saiu com sucesso.')
    return redirect('login')


@login_required
def index(request):
    fotos = FotoCapturada.objects.filter(usuario=request.user)[:10]  # Últimas 10 fotos do usuário
    return render(request, 'core/index.html', {'fotos': fotos})


@login_required
def capturar_foto(request):
    return render(request, 'core/capturar_foto.html')


@csrf_exempt
@login_required
def salvar_foto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nome = data.get('nome', '').strip()
            imagem_data = data.get('imagem', '')

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome é obrigatório'})

            if not imagem_data:
                return JsonResponse({'success': False, 'error': 'Imagem é obrigatória'})

            # Remove o prefixo data:image/jpeg;base64, se existir
            if imagem_data.startswith('data:image'):
                imagem_data = imagem_data.split(',')[1]

            # Decodifica a imagem base64
            image_data = base64.b64decode(imagem_data)
            image_file = ContentFile(image_data, name=f'{nome}_{request.user.id}_{len(FotoCapturada.objects.filter(usuario=request.user)) + 1}.jpg')

            # Salva no banco de dados associado ao usuário logado
            foto = FotoCapturada(usuario=request.user, nome=nome, imagem=image_file)
            foto.save()

            return JsonResponse({
                'success': True,
                'message': f'Foto de {nome} salva com sucesso!',
                'redirect_url': '/'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método não permitido'})
