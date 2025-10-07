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


def pode_criar_usuarios(usuario):
    """Verifica se o usuário tem permissão para criar outros usuários"""
    if not usuario.is_authenticated:
        return False
    
    # Admin pode criar qualquer tipo
    if usuario.is_staff or usuario.is_superuser:
        return True
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return False
    
    # Ministro e Diretor podem criar usuários
    return usuario.perfil.tipo_perfil in ['MINISTRO', 'DIRETOR']


def obter_perfis_permitidos(usuario):
    """
    Retorna lista de tipos de perfil que o usuário pode criar.
    Retorna tuplas (valor, label) para usar em select.
    """
    if not usuario.is_authenticated:
        return []
    
    # Admin/Superuser podem criar qualquer tipo
    if usuario.is_staff or usuario.is_superuser:
        return [
            ('COMUM', '👤 Usuário Comum'),
            ('DIRETOR', '👔 Diretor de Divisões'),
            ('MINISTRO', '🎖️ Ministro do Meio Ambiente'),
        ]
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return []
    
    # Ministro pode criar Ministros, Diretores e Comuns
    if usuario.perfil.tipo_perfil == 'MINISTRO':
        return [
            ('COMUM', '👤 Usuário Comum'),
            ('DIRETOR', '👔 Diretor de Divisões'),
            ('MINISTRO', '🎖️ Ministro do Meio Ambiente'),
        ]
    
    # Diretor pode criar Diretores e Comuns
    if usuario.perfil.tipo_perfil == 'DIRETOR':
        return [
            ('COMUM', '👤 Usuário Comum'),
            ('DIRETOR', '👔 Diretor de Divisões'),
        ]
    
    # Usuário comum não pode criar ninguém
    return []


def obter_niveis_visualizacao(usuario):
    """
    Retorna lista de níveis de impacto que o usuário pode visualizar.
    """
    if not usuario.is_authenticated:
        return []
    
    # Admin/Superuser podem ver todos
    if usuario.is_staff or usuario.is_superuser:
        return [1, 2, 3]
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return [1]  # Padrão: apenas nível 1
    
    # Ministro pode ver todos os níveis
    if usuario.perfil.tipo_perfil == 'MINISTRO':
        return [1, 2, 3]
    
    # Diretor pode ver níveis 1 e 2
    if usuario.perfil.tipo_perfil == 'DIRETOR':
        return [1, 2]
    
    # Usuário comum pode ver apenas nível 1
    return [1]


def obter_niveis_criacao(usuario):
    """
    Retorna lista de níveis de impacto que o usuário pode criar.
    Retorna tuplas (valor, label) para usar em select.
    """
    if not usuario.is_authenticated:
        return []
    
    # Admin/Superuser podem criar todos
    if usuario.is_staff or usuario.is_superuser:
        return [
            (1, 'Nível 1 - Baixo Impacto'),
            (2, 'Nível 2 - Médio Impacto'),
            (3, 'Nível 3 - Alto Impacto'),
        ]
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return []
    
    # Ministro pode criar todos os níveis
    if usuario.perfil.tipo_perfil == 'MINISTRO':
        return [
            (1, 'Nível 1 - Baixo Impacto'),
            (2, 'Nível 2 - Médio Impacto'),
            (3, 'Nível 3 - Alto Impacto'),
        ]
    
    # Diretor pode criar níveis 1 e 2
    if usuario.perfil.tipo_perfil == 'DIRETOR':
        return [
            (1, 'Nível 1 - Baixo Impacto'),
            (2, 'Nível 2 - Médio Impacto'),
        ]
    
    # Usuário comum não pode criar propriedades
    return []


def pode_criar_propriedades(usuario):
    """Verifica se o usuário tem permissão para criar propriedades"""
    if not usuario.is_authenticated:
        return False
    
    # Admin pode criar
    if usuario.is_staff or usuario.is_superuser:
        return True
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return False
    
    # Ministro e Diretor podem criar propriedades
    # Usuário comum NÃO pode criar
    return usuario.perfil.tipo_perfil in ['MINISTRO', 'DIRETOR']


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


def preprocessar_imagem_opencv(image_np):
    """
    Pré-processa imagem com OpenCV para melhorar reconhecimento facial.
    """
    import cv2
    import numpy as np
    
    try:
        # 1. Converter RGB para BGR (OpenCV usa BGR)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # 2. Avaliar qualidade da imagem
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # 2.1 Detectar blur (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < 30:  # Threshold mais permissivo
            return None, blur_score, f"Imagem desfocada (score: {blur_score:.1f}). Use uma imagem mais nítida."
        
        # 2.2 Verificar brilho médio
        brightness = np.mean(gray)
        if brightness < 30:
            return None, brightness, "Imagem muito escura. Melhore a iluminação."
        if brightness > 240:
            return None, brightness, "Imagem muito clara. Reduza a iluminação."
        
        # 3. Equalização adaptativa de histograma (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Aplicar em cada canal de cor
        b, g, r = cv2.split(image_bgr)
        b_clahe = clahe.apply(b)
        g_clahe = clahe.apply(g)
        r_clahe = clahe.apply(r)
        image_clahe = cv2.merge([b_clahe, g_clahe, r_clahe])
        
        # 4. Redução de ruído (Denoising)
        image_denoised = cv2.fastNlMeansDenoisingColored(
            image_clahe, 
            None, 
            h=10,
            hColor=10,
            templateWindowSize=7,
            searchWindowSize=21
        )
        
        # 5. Aumentar nitidez (Sharpening)
        kernel_sharpening = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])
        image_sharp = cv2.filter2D(image_denoised, -1, kernel_sharpening)
        
        # 6. Ajustar gamma para melhorar contraste
        def adjust_gamma(image, gamma=1.2):
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 
                            for i in np.arange(0, 256)]).astype("uint8")
            return cv2.LUT(image, table)
        
        image_gamma = adjust_gamma(image_sharp, gamma=1.2)
        
        # 7. Converter de volta para RGB (para face_recognition)
        image_processed = cv2.cvtColor(image_gamma, cv2.COLOR_BGR2RGB)
        
        # Calcular score de qualidade final
        quality_score = min(100, (blur_score / 5) + (50 if 60 < brightness < 200 else 0))
        
        return image_processed, quality_score, None
        
    except Exception as e:
        return None, 0, f"Erro no pré-processamento: {str(e)}"


def detectar_qualidade_imagem(image_np):
    """
    Detecta qualidade da imagem e retorna score + sugestões.
    """
    import cv2
    import numpy as np
    
    sugestoes = []
    score = 100
    
    # Converter para BGR e grayscale
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Verificar nitidez (blur)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < 30:
        score -= 30
        sugestoes.append("Imagem desfocada - segure a câmera com firmeza")
    elif blur_score < 60:
        score -= 15
        sugestoes.append("Imagem levemente desfocada")
    
    # 2. Verificar iluminação
    brightness = np.mean(gray)
    if brightness < 40:
        score -= 25
        sugestoes.append("Ambiente muito escuro - aumente a iluminação")
    elif brightness < 60:
        score -= 10
        sugestoes.append("Iluminação baixa")
    elif brightness > 220:
        score -= 20
        sugestoes.append("Ambiente muito claro - reduza a luz")
    elif brightness > 200:
        score -= 10
        sugestoes.append("Iluminação alta")
    
    # 3. Verificar contraste
    contrast = gray.std()
    if contrast < 25:
        score -= 15
        sugestoes.append("Baixo contraste - melhore a iluminação")
    
    # 4. Verificar se imagem está muito pixelada
    height, width = gray.shape
    if height < 240 or width < 320:
        score -= 20
        sugestoes.append("Resolução baixa - use câmera melhor")
    
    qualidade_ok = score >= 40  # Threshold mais permissivo
    
    if not sugestoes:
        sugestoes.append("Qualidade de imagem boa!")
    
    return qualidade_ok, score, sugestoes


def detectar_liveness(image_np):
    """
    Detecta se a imagem é de uma pessoa real (liveness detection).
    Implementação simplificada usando análise de textura e variação de pixels.
    """
    import cv2
    import numpy as np
    
    try:
        # Converter para BGR e grayscale
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        score = 100
        reasons = []
        
        # 1. Análise de textura (LBP - Local Binary Pattern simplificado)
        # Imagens de telas/fotos tendem a ter menos variação de textura
        texture_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        if texture_variance < 50:
            score -= 40
            reasons.append("Textura suspeita (possível foto de foto)")
        
        # 2. Análise de brilho especular
        # Telas de celular/monitor tem brilho mais uniforme
        brightness_std = gray.std()
        if brightness_std < 30:
            score -= 30
            reasons.append("Brilho muito uniforme (possível tela)")
        
        # 3. Detecção de bordas (fotos tendem a ter bordas abruptas)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        if edge_density > 0.15:  # Muitas bordas podem indicar foto de foto
            score -= 20
            reasons.append("Muitas bordas detectadas")
        
        # 4. Análise de cores (telas tem gama de cores diferente)
        color_std = np.std(image_np, axis=(0, 1))
        if np.mean(color_std) < 20:
            score -= 25
            reasons.append("Variação de cor suspeita")
        
        # Decidir se passa no teste
        is_live = score >= 50
        
        if is_live:
            reason = "Imagem válida"
        else:
            reason = " | ".join(reasons)
        
        return {
            'is_live': is_live,
            'score': score,
            'reason': reason
        }
        
    except Exception as e:
        # Em caso de erro, permitir por segurança (para não bloquear usuários legítimos)
        return {
            'is_live': True,
            'score': 100,
            'reason': f'Erro na detecção: {str(e)}'
        }


@csrf_exempt
def reconhecer_face(request):
    """Processa a imagem capturada e tenta reconhecer o usuário"""
    # Import lazy para evitar problemas na inicialização do Django
    # import cv2
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
        
        # Verificar qualidade da imagem
        qualidade_ok, quality_score, sugestoes = detectar_qualidade_imagem(image_np)
        
        if not qualidade_ok:
            return JsonResponse({
                'success': False,
                'message': 'Qualidade da imagem inadequada.',
                'quality_score': quality_score,
                'suggestions': sugestoes
            })
        
        # Pré-processar com OpenCV
        image_processed, process_score, error_msg = preprocessar_imagem_opencv(image_np)
        
        if image_processed is None:
            return JsonResponse({
                'success': False,
                'message': error_msg,
                'quality_score': process_score
            })
        
        # Usar imagem processada para detecção
        image_np = image_processed
        
        # === DETECÇÃO DE LIVENESS (ANTI-SPOOFING) ===
        liveness_result = detectar_liveness(image_np)
        if not liveness_result['is_live']:
            return JsonResponse({
                'success': False,
                'message': f'Detecção de fraude: {liveness_result["reason"]}'
            })
        
        # Detectar faces na imagem capturada
        face_locations = face_recognition.face_locations(image_np)
        
        if not face_locations:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum rosto detectado. Por favor, posicione seu rosto na câmera.',
                'suggestions': ['Centralize seu rosto na câmera', 'Melhore a iluminação']
            })
        
        if len(face_locations) > 1:
            return JsonResponse({
                'success': False,
                'message': 'Múltiplos rostos detectados. Certifique-se de estar sozinho na câmera.',
                'suggestions': ['Apenas uma pessoa deve aparecer', 'Afaste outras pessoas']
            })
        
        # Extrair encoding da face capturada
        face_encodings = face_recognition.face_encodings(image_np, face_locations)
        if not face_encodings:
            return JsonResponse({
                'success': False,
                'message': 'Não foi possível processar o rosto detectado.',
                'suggestions': ['Tente novamente', 'Melhore a iluminação']
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
        
        # Tolerância dinâmica baseada na qualidade
        if quality_score >= 80:
            tolerancia = 0.60  # Rigoroso para imagens boas
        elif quality_score >= 60:
            tolerancia = 0.65  # Médio
        else:
            tolerancia = 0.70  # Mais permissivo para imagens ruins
        
        # Comparar com cada usuário cadastrado
        for perfil in usuarios_com_foto:
            try:
                # Carregar foto do perfil
                perfil_image = face_recognition.load_image_file(perfil.foto.path)
                
                # Pré-processar foto do perfil também
                perfil_processed, _, _ = preprocessar_imagem_opencv(perfil_image)
                if perfil_processed is not None:
                    perfil_image = perfil_processed
                
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
            
            # Validar confiança mínima (ajustada pela qualidade)
            confianca_minima = 50 if quality_score >= 70 else 45
            
            if confianca_percentual < confianca_minima:
                return JsonResponse({
                    'success': False,
                    'message': f'Confiança muito baixa ({confianca_percentual:.1f}%). Tente novamente.',
                    'confidence': f'{confianca_percentual:.1f}%',
                    'quality_score': quality_score,
                    'suggestions': sugestoes + ['Tente capturar novamente', 'Melhore as condições']
                })
            
            # Fazer login do usuário
            login(request, melhor_match, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'success': True,
                'message': f'Bem-vindo(a), {melhor_match.get_full_name() or melhor_match.username}!',
                'username': melhor_match.username,
                'confidence': f'{confianca_percentual:.1f}%',
                'quality_score': quality_score,
                'liveness_score': f'{liveness_result["score"]:.1f}',
                'processing': 'OpenCV enhanced'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Rosto não reconhecido. Tente novamente ou use login com senha.',
                'quality_score': quality_score,
                'suggestions': sugestoes + ['Use login com senha', 'Tente com melhor iluminação']
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Erro ao processar reconhecimento facial: {str(e)}'
        }, status=500)


@login_required
def index(request):
    # Verificar permissões do usuário
    pode_criar_usuarios_flag = pode_criar_usuarios(request.user)
    pode_criar_propriedades_flag = pode_criar_propriedades(request.user)
    
    # Obter níveis de visualização permitidos para o usuário
    niveis_permitidos = obter_niveis_visualizacao(request.user)
    
    # Estatísticas para o dashboard
    total_usuarios = User.objects.count()
    
    # Filtrar propriedades por nível de permissão
    total_propriedades = PropriedadeRural.objects.filter(
        ativo=True,
        nivel_impacto__in=niveis_permitidos
    ).count()
    
    # Últimas propriedades cadastradas (filtradas por nível de permissão)
    ultimas_propriedades = PropriedadeRural.objects.filter(
        ativo=True,
        nivel_impacto__in=niveis_permitidos
    ).order_by('-data_cadastro')[:5]
    
    # Últimos usuários cadastrados (se for admin)
    ultimos_usuarios = None
    if request.user.is_staff:
        ultimos_usuarios = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_propriedades': total_propriedades,
        'ultimas_propriedades': ultimas_propriedades,
        'ultimos_usuarios': ultimos_usuarios,
        'pode_criar_usuarios': pode_criar_usuarios_flag,
        'pode_criar_propriedades': pode_criar_propriedades_flag,
    }
    
    return render(request, 'core/index.html', context)


# CRUD de Propriedades Rurais

@login_required
def propriedades_list(request):
    """Lista todas as propriedades rurais"""
    nivel_filtro = request.GET.get('nivel')
    search = request.GET.get('search', '')
    
    propriedades = PropriedadeRural.objects.filter(ativo=True)
    
    # Filtrar por níveis que o usuário pode visualizar
    niveis_permitidos = obter_niveis_visualizacao(request.user)
    propriedades = propriedades.filter(nivel_impacto__in=niveis_permitidos)
    
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
        'pode_criar': pode_criar_propriedades(request.user),
        'niveis_permitidos': niveis_permitidos,
    }
    return render(request, 'core/propriedades_list.html', context)


@login_required
def propriedade_detail(request, pk):
    """Visualiza detalhes de uma propriedade"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    
    # Verificar se usuário tem permissão para ver este nível
    niveis_permitidos = obter_niveis_visualizacao(request.user)
    if propriedade.nivel_impacto not in niveis_permitidos:
        messages.error(request, 'Você não tem permissão para visualizar propriedades deste nível!')
        return redirect('propriedades_list')
    
    return render(request, 'core/propriedade_detail.html', {'propriedade': propriedade})


@login_required
def propriedade_create(request):
    """Cria uma nova propriedade"""
    # Verificar se usuário pode criar propriedades
    if not pode_criar_propriedades(request.user):
        messages.error(request, 'Você não tem permissão para cadastrar propriedades!')
        return redirect('propriedades_list')
    
    niveis_permitidos = obter_niveis_criacao(request.user)
    
    if request.method == 'POST':
        try:
            nivel_escolhido = int(request.POST.get('nivel_impacto'))
            
            # Validar se o nível escolhido é permitido
            niveis_valores = [n[0] for n in niveis_permitidos]
            if nivel_escolhido not in niveis_valores:
                messages.error(request, 'Você não tem permissão para cadastrar propriedades neste nível!')
                return render(request, 'core/propriedade_form.html', {
                    'niveis_permitidos': niveis_permitidos
                })
            
            propriedade = PropriedadeRural(
                nome_propriedade=request.POST.get('nome_propriedade'),
                proprietario=request.POST.get('proprietario'),
                cpf_cnpj=request.POST.get('cpf_cnpj'),
                endereco=request.POST.get('endereco'),
                cidade=request.POST.get('cidade'),
                estado=request.POST.get('estado'),
                area_hectares=request.POST.get('area_hectares'),
                agrotoxico_utilizado=request.POST.get('agrotoxico_utilizado'),
                nivel_impacto=nivel_escolhido,
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
    
    return render(request, 'core/propriedade_form.html', {
        'niveis_permitidos': niveis_permitidos
    })


@login_required
def propriedade_update(request, pk):
    """Atualiza uma propriedade existente"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    
    # Verificar se usuário pode ver/editar este nível
    niveis_permitidos = obter_niveis_criacao(request.user)
    niveis_valores = [n[0] for n in niveis_permitidos]
    
    if propriedade.nivel_impacto not in niveis_valores:
        messages.error(request, 'Você não tem permissão para editar propriedades deste nível!')
        return redirect('propriedades_list')
    
    if request.method == 'POST':
        try:
            nivel_escolhido = int(request.POST.get('nivel_impacto'))
            
            # Validar se o novo nível é permitido
            if nivel_escolhido not in niveis_valores:
                messages.error(request, 'Você não tem permissão para alterar para este nível!')
                return render(request, 'core/propriedade_form.html', {
                    'propriedade': propriedade,
                    'niveis_permitidos': niveis_permitidos
                })
            
            propriedade.nome_propriedade = request.POST.get('nome_propriedade')
            propriedade.proprietario = request.POST.get('proprietario')
            propriedade.cpf_cnpj = request.POST.get('cpf_cnpj')
            propriedade.endereco = request.POST.get('endereco')
            propriedade.cidade = request.POST.get('cidade')
            propriedade.estado = request.POST.get('estado')
            propriedade.area_hectares = request.POST.get('area_hectares')
            propriedade.agrotoxico_utilizado = request.POST.get('agrotoxico_utilizado')
            propriedade.nivel_impacto = nivel_escolhido
            propriedade.descricao_impacto = request.POST.get('descricao_impacto')
            propriedade.data_identificacao = request.POST.get('data_identificacao')
            propriedade.latitude = request.POST.get('latitude') or None
            propriedade.longitude = request.POST.get('longitude') or None
            propriedade.save()
            
            messages.success(request, 'Propriedade atualizada com sucesso!')
            return redirect('propriedade_detail', pk=propriedade.pk)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar propriedade: {str(e)}')
    
    return render(request, 'core/propriedade_form.html', {
        'propriedade': propriedade,
        'niveis_permitidos': niveis_permitidos
    })


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
        'pode_criar': pode_criar_usuarios(request.user),
    }
    return render(request, 'core/usuarios_list.html', context)


@login_required
def usuario_detail(request, pk):
    """Visualiza detalhes de um usuário"""
    usuario = get_object_or_404(User, pk=pk)
    return render(request, 'core/usuario_detail.html', {'usuario_perfil': usuario})


def usuario_create(request):
    """Cria um novo usuário com foto"""
    # Verificar se é um usuário autenticado criando outro usuário
    is_admin_creating = request.user.is_authenticated and pode_criar_usuarios(request.user)
    perfis_permitidos = obter_perfis_permitidos(request.user) if is_admin_creating else []
    
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
                return render(request, 'core/usuario_form.html', {
                    'is_admin_creating': is_admin_creating,
                    'perfis_permitidos': perfis_permitidos
                })
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Nome de usuário já existe!')
                return render(request, 'core/usuario_form.html', {
                    'is_admin_creating': is_admin_creating,
                    'perfis_permitidos': perfis_permitidos
                })
            
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
            
            # Determinar tipo de perfil
            if is_admin_creating:
                # Usuário logado com permissão pode escolher o tipo
                tipo_perfil_escolhido = request.POST.get('tipo_perfil', 'COMUM')
                
                # Validar se o tipo escolhido é permitido para este usuário
                perfis_valores = [p[0] for p in perfis_permitidos]
                if tipo_perfil_escolhido in perfis_valores:
                    perfil.tipo_perfil = tipo_perfil_escolhido
                else:
                    perfil.tipo_perfil = 'COMUM'
                    messages.warning(request, 'Tipo de perfil inválido. Definido como Usuário Comum.')
            else:
                # Auto-cadastro: sempre é Usuário Comum
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
            
            # Se for admin criando, redireciona para lista
            if is_admin_creating:
                return redirect('usuarios_list')
            
            # Se for auto-cadastro, faz login automático
            user_authenticated = authenticate(username=username, password=password)
            if user_authenticated:
                login(request, user_authenticated)
                return redirect('index')
            
            return redirect('login')
            
        except IntegrityError as e:
            messages.error(request, 'Erro: CPF já cadastrado!')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar usuário: {str(e)}')
    
    return render(request, 'core/usuario_form.html', {
        'is_admin_creating': is_admin_creating,
        'perfis_permitidos': perfis_permitidos
    })


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
