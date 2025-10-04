from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
import base64
from .models import PropriedadeRural, PerfilUsuario


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


def login_facial_view(request):
    """View para login com reconhecimento facial"""
    if request.user.is_authenticated:
        return redirect('index')
    
    return render(request, 'core/login_facial.html')


@csrf_exempt
def reconhecer_face(request):
    """Processa a imagem capturada e tenta reconhecer o usuário"""
    # Import lazy para evitar problemas na inicialização do Django
    import cv2
    import face_recognition
    import numpy as np
    from PIL import Image
    import io
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        # Obter imagem da requisição
        foto_data = request.POST.get('foto_base64')
        if not foto_data:
            return JsonResponse({'error': 'Nenhuma imagem fornecida'}, status=400)
        
        # Remover o prefixo data:image se existir
        if foto_data.startswith('data:image'):
            foto_data = foto_data.split(',')[1]
        
        # Decodificar imagem
        image_data = base64.b64decode(foto_data)
        image = Image.open(io.BytesIO(image_data))
        
        # Converter para RGB (necessário para face_recognition)
        image_rgb = image.convert('RGB')
        image_np = np.array(image_rgb)
        
        # Detectar faces na imagem capturada
        face_locations = face_recognition.face_locations(image_np)
        
        if not face_locations:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum rosto detectado. Por favor, posicione seu rosto na câmera.'
            })
        
        if len(face_locations) > 1:
            return JsonResponse({
                'success': False,
                'message': 'Múltiplos rostos detectados. Certifique-se de estar sozinho na câmera.'
            })
        
        # Extrair encoding da face capturada
        face_encodings = face_recognition.face_encodings(image_np, face_locations)
        if not face_encodings:
            return JsonResponse({
                'success': False,
                'message': 'Não foi possível processar o rosto detectado.'
            })
        
        captured_encoding = face_encodings[0]
        
        # Buscar todos os usuários com foto de perfil
        usuarios_com_foto = PerfilUsuario.objects.exclude(foto__isnull=True).exclude(foto='')
        
        if not usuarios_com_foto.exists():
            return JsonResponse({
                'success': False,
                'message': 'Nenhum usuário cadastrado com foto de perfil.'
            })
        
        melhor_match = None
        menor_distancia = float('inf')
        tolerancia = 0.6  # Quanto menor, mais rigoroso
        
        # Comparar com cada usuário cadastrado
        for perfil in usuarios_com_foto:
            try:
                # Carregar foto do perfil
                perfil_image = face_recognition.load_image_file(perfil.foto.path)
                
                # Detectar face na foto do perfil
                perfil_face_locations = face_recognition.face_locations(perfil_image)
                
                if not perfil_face_locations:
                    continue
                
                # Extrair encoding da face do perfil
                perfil_encodings = face_recognition.face_encodings(perfil_image, perfil_face_locations)
                
                if not perfil_encodings:
                    continue
                
                perfil_encoding = perfil_encodings[0]
                
                # Calcular distância entre as faces
                face_distance = face_recognition.face_distance([perfil_encoding], captured_encoding)[0]
                
                # Verificar se é o melhor match até agora
                if face_distance < menor_distancia and face_distance < tolerancia:
                    menor_distancia = face_distance
                    melhor_match = perfil.usuario
                    
            except Exception as e:
                print(f"Erro ao processar perfil {perfil.usuario.username}: {str(e)}")
                continue
        
        # Se encontrou um match
        if melhor_match:
            # Calcular confiança do reconhecimento
            confianca_percentual = (1 - menor_distancia) * 100
            
            # Validar confiança mínima de 60%
            if confianca_percentual < 60:
                return JsonResponse({
                    'success': False,
                    'message': f'Confiança muito baixa ({confianca_percentual:.1f}%). Tente novamente com melhor iluminação ou use login com senha.'
                })
            
            # Fazer login do usuário
            login(request, melhor_match, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'success': True,
                'message': f'Bem-vindo(a), {melhor_match.get_full_name() or melhor_match.username}!',
                'username': melhor_match.username,
                'confidence': f'{confianca_percentual:.1f}%'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Rosto não reconhecido. Tente novamente ou use login com senha.'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Erro ao processar reconhecimento facial: {str(e)}'
        }, status=500)


@login_required
def index(request):
    # Estatísticas para o dashboard
    total_usuarios = User.objects.count()
    total_propriedades = PropriedadeRural.objects.filter(ativo=True).count()
    
    # Últimas propriedades cadastradas (apenas ativas)
    ultimas_propriedades = PropriedadeRural.objects.filter(ativo=True).order_by('-data_cadastro')[:5]
    
    # Últimos usuários cadastrados (se for admin)
    ultimos_usuarios = None
    if request.user.is_staff:
        ultimos_usuarios = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_propriedades': total_propriedades,
        'ultimas_propriedades': ultimas_propriedades,
        'ultimos_usuarios': ultimos_usuarios,
    }
    
    return render(request, 'core/index.html', context)


# CRUD de Propriedades Rurais

@login_required
def propriedades_list(request):
    """Lista todas as propriedades rurais"""
    nivel_filtro = request.GET.get('nivel')
    search = request.GET.get('search', '')
    
    propriedades = PropriedadeRural.objects.filter(ativo=True)
    
    if nivel_filtro:
        propriedades = propriedades.filter(nivel_impacto=nivel_filtro)
    
    if search:
        propriedades = propriedades.filter(
            nome_propriedade__icontains=search
        ) | propriedades.filter(
            proprietario__icontains=search
        ) | propriedades.filter(
            cidade__icontains=search
        )
    
    paginator = Paginator(propriedades, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'nivel_filtro': nivel_filtro,
        'search': search,
    }
    return render(request, 'core/propriedades_list.html', context)


@login_required
def propriedade_detail(request, pk):
    """Visualiza detalhes de uma propriedade"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    return render(request, 'core/propriedade_detail.html', {'propriedade': propriedade})


@login_required
def propriedade_create(request):
    """Cria uma nova propriedade"""
    if request.method == 'POST':
        try:
            propriedade = PropriedadeRural(
                nome_propriedade=request.POST.get('nome_propriedade'),
                proprietario=request.POST.get('proprietario'),
                cpf_cnpj=request.POST.get('cpf_cnpj'),
                endereco=request.POST.get('endereco'),
                cidade=request.POST.get('cidade'),
                estado=request.POST.get('estado'),
                area_hectares=request.POST.get('area_hectares'),
                agrotoxico_utilizado=request.POST.get('agrotoxico_utilizado'),
                nivel_impacto=request.POST.get('nivel_impacto'),
                descricao_impacto=request.POST.get('descricao_impacto'),
                data_identificacao=request.POST.get('data_identificacao'),
                latitude=request.POST.get('latitude') or None,
                longitude=request.POST.get('longitude') or None,
                usuario_cadastro=request.user
            )
            propriedade.save()
            messages.success(request, 'Propriedade cadastrada com sucesso!')
            return redirect('propriedade_detail', pk=propriedade.pk)
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar propriedade: {str(e)}')
    
    return render(request, 'core/propriedade_form.html')


@login_required
def propriedade_update(request, pk):
    """Atualiza uma propriedade existente"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    
    if request.method == 'POST':
        try:
            propriedade.nome_propriedade = request.POST.get('nome_propriedade')
            propriedade.proprietario = request.POST.get('proprietario')
            propriedade.cpf_cnpj = request.POST.get('cpf_cnpj')
            propriedade.endereco = request.POST.get('endereco')
            propriedade.cidade = request.POST.get('cidade')
            propriedade.estado = request.POST.get('estado')
            propriedade.area_hectares = request.POST.get('area_hectares')
            propriedade.agrotoxico_utilizado = request.POST.get('agrotoxico_utilizado')
            propriedade.nivel_impacto = request.POST.get('nivel_impacto')
            propriedade.descricao_impacto = request.POST.get('descricao_impacto')
            propriedade.data_identificacao = request.POST.get('data_identificacao')
            propriedade.latitude = request.POST.get('latitude') or None
            propriedade.longitude = request.POST.get('longitude') or None
            propriedade.save()
            
            messages.success(request, 'Propriedade atualizada com sucesso!')
            return redirect('propriedade_detail', pk=propriedade.pk)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar propriedade: {str(e)}')
    
    return render(request, 'core/propriedade_form.html', {'propriedade': propriedade})


@login_required
def propriedade_delete(request, pk):
    """Deleta (desativa) uma propriedade"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    
    if request.method == 'POST':
        propriedade.ativo = False
        propriedade.save()
        messages.success(request, 'Propriedade removida com sucesso!')
        return redirect('propriedades_list')
    
    return render(request, 'core/propriedade_confirm_delete.html', {'propriedade': propriedade})


# CRUD de Usuários

@login_required
def usuarios_list(request):
    """Lista todos os usuários"""
    search = request.GET.get('search', '')
    
    usuarios = User.objects.all()
    
    if search:
        usuarios = usuarios.filter(
            username__icontains=search
        ) | usuarios.filter(
            first_name__icontains=search
        ) | usuarios.filter(
            last_name__icontains=search
        ) | usuarios.filter(
            email__icontains=search
        )
    
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'core/usuarios_list.html', context)


@login_required
def usuario_detail(request, pk):
    """Visualiza detalhes de um usuário"""
    usuario = get_object_or_404(User, pk=pk)
    return render(request, 'core/usuario_detail.html', {'usuario_perfil': usuario})


def usuario_create(request):
    """Cria um novo usuário com foto"""
    if request.method == 'POST':
        try:
            # Dados do usuário
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            
            # Validações
            if password != password_confirm:
                messages.error(request, 'As senhas não coincidem!')
                return render(request, 'core/usuario_form.html')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Nome de usuário já existe!')
                return render(request, 'core/usuario_form.html')
            
            # Criar usuário
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Atualizar perfil
            perfil = user.perfil
            # Novos cadastros sempre são Usuário Comum
            perfil.tipo_perfil = 'COMUM'
            perfil.telefone = request.POST.get('telefone', '')
            perfil.cpf = request.POST.get('cpf', '') or None
            perfil.data_nascimento = request.POST.get('data_nascimento') or None
            perfil.endereco = request.POST.get('endereco', '')
            perfil.bio = request.POST.get('bio', '')
            
            # Processar foto (base64)
            foto_data = request.POST.get('foto_base64')
            if foto_data:
                if foto_data.startswith('data:image'):
                    foto_data = foto_data.split(',')[1]
                image_data = base64.b64decode(foto_data)
                image_file = ContentFile(image_data, name=f'{username}_foto.jpg')
                perfil.foto = image_file
            
            perfil.save()
            
            messages.success(request, f'Usuário {username} cadastrado com sucesso!')
            
            # Fazer login automático
            user_authenticated = authenticate(username=username, password=password)
            if user_authenticated:
                login(request, user_authenticated)
                return redirect('index')
            
            return redirect('login')
            
        except IntegrityError as e:
            messages.error(request, 'Erro: CPF já cadastrado!')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar usuário: {str(e)}')
    
    return render(request, 'core/usuario_form.html')


@login_required
def usuario_update(request, pk):
    """Atualiza um usuário existente"""
    usuario = get_object_or_404(User, pk=pk)
    
    # Apenas admin ou o próprio usuário pode editar
    if not request.user.is_staff and request.user.pk != pk:
        messages.error(request, 'Você não tem permissão para editar este usuário!')
        return redirect('usuarios_list')
    
    if request.method == 'POST':
        try:
            # Atualizar dados do usuário
            usuario.first_name = request.POST.get('first_name')
            usuario.last_name = request.POST.get('last_name')
            usuario.email = request.POST.get('email')
            
            # Atualizar senha se fornecida
            new_password = request.POST.get('new_password')
            if new_password:
                password_confirm = request.POST.get('password_confirm')
                if new_password == password_confirm:
                    usuario.set_password(new_password)
                else:
                    messages.error(request, 'As senhas não coincidem!')
                    return render(request, 'core/usuario_form.html', {'usuario_perfil': usuario})
            
            usuario.save()
            
            # Atualizar perfil (criar se não existir)
            try:
                perfil = usuario.perfil
            except PerfilUsuario.DoesNotExist:
                # Criar perfil se não existir
                perfil = PerfilUsuario.objects.create(usuario=usuario)
            
            # Apenas admin pode alterar o tipo de perfil
            if request.user.is_staff:
                perfil.tipo_perfil = request.POST.get('tipo_perfil', perfil.tipo_perfil)
            
            perfil.telefone = request.POST.get('telefone', '')
            cpf = request.POST.get('cpf', '') or None
            if cpf and cpf != perfil.cpf:
                if PerfilUsuario.objects.filter(cpf=cpf).exclude(usuario=usuario).exists():
                    messages.error(request, 'CPF já cadastrado para outro usuário!')
                    return render(request, 'core/usuario_form.html', {'usuario_perfil': usuario})
                perfil.cpf = cpf
            
            perfil.data_nascimento = request.POST.get('data_nascimento') or None
            perfil.endereco = request.POST.get('endereco', '')
            perfil.bio = request.POST.get('bio', '')
            
            # Verificar se deve deletar a foto
            delete_foto = request.POST.get('delete_foto')
            if delete_foto == 'true':
                if perfil.foto:
                    perfil.foto.delete()
                    perfil.foto = None
            
            # Processar nova foto se fornecida
            foto_data = request.POST.get('foto_base64')
            if foto_data:
                if foto_data.startswith('data:image'):
                    foto_data = foto_data.split(',')[1]
                image_data = base64.b64decode(foto_data)
                image_file = ContentFile(image_data, name=f'{usuario.username}_foto.jpg')
                perfil.foto = image_file
            
            perfil.save()
            
            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('usuario_detail', pk=usuario.pk)
            
        except IntegrityError:
            messages.error(request, 'Erro: CPF já cadastrado!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar usuário: {str(e)}')
    
    return render(request, 'core/usuario_form.html', {'usuario_perfil': usuario})


@login_required
def usuario_delete(request, pk):
    """Deleta um usuário"""
    usuario = get_object_or_404(User, pk=pk)
    
    # Apenas admin pode deletar
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para excluir usuários!')
        return redirect('usuarios_list')
    
    # Não permitir deletar a si mesmo
    if request.user.pk == pk:
        messages.error(request, 'Você não pode excluir sua própria conta!')
        return redirect('usuarios_list')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuário {username} removido com sucesso!')
        return redirect('usuarios_list')
    
    return render(request, 'core/usuario_confirm_delete.html', {'usuario_perfil': usuario})
