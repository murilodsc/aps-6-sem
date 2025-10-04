from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """Perfil estendido do usuário com foto e tipo de perfil"""
    
    TIPO_PERFIL_CHOICES = [
        ('COMUM', 'Usuário Comum'),
        ('DIRETOR', 'Diretor de Divisões'),
        ('MINISTRO', 'Ministro do Meio Ambiente'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_perfil = models.CharField(
        max_length=10,
        choices=TIPO_PERFIL_CHOICES,
        default='COMUM',
        verbose_name="Tipo de Perfil"
    )
    foto = models.ImageField(upload_to='fotos_usuarios/', verbose_name="Foto do Usuário", null=True, blank=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone", blank=True)
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True, unique=True, null=True)
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", null=True, blank=True)
    endereco = models.TextField(verbose_name="Endereço", blank=True)
    bio = models.TextField(verbose_name="Biografia", blank=True, max_length=500)
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    def get_tipo_perfil_display_icon(self):
        """Retorna o ícone correspondente ao tipo de perfil"""
        icons = {
            'COMUM': '👤',
            'DIRETOR': '👔',
            'MINISTRO': '🎖️',
        }
        return icons.get(self.tipo_perfil, '👤')
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"
        ordering = ['-data_cadastro']


@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil quando um usuário é criado"""
    if created:
        PerfilUsuario.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def salvar_perfil_usuario(sender, instance, **kwargs):
    """Salva o perfil quando o usuário é salvo"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


class FotoCapturada(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário associado à foto")
    nome = models.CharField(max_length=100, help_text="Nome da pessoa")
    imagem = models.ImageField(upload_to='fotos_capturadas/', help_text="Foto capturada")
    data_captura = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nome} ({self.usuario.username}) - {self.data_captura.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Foto Capturada"
        verbose_name_plural = "Fotos Capturadas"
        ordering = ['-data_captura']


class PropriedadeRural(models.Model):
    NIVEL_CHOICES = [
        (1, 'Nível 1 - Baixo Impacto'),
        (2, 'Nível 2 - Médio Impacto'),
        (3, 'Nível 3 - Alto Impacto'),
    ]

    nome_propriedade = models.CharField(max_length=200, verbose_name="Nome da Propriedade")
    proprietario = models.CharField(max_length=200, verbose_name="Nome do Proprietário")
    cpf_cnpj = models.CharField(max_length=18, verbose_name="CPF/CNPJ")
    endereco = models.TextField(verbose_name="Endereço Completo")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=2, verbose_name="Estado (UF)")
    area_hectares = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Área em Hectares"
    )
    
    agrotoxico_utilizado = models.CharField(max_length=200, verbose_name="Agrotóxico Proibido Utilizado")
    nivel_impacto = models.IntegerField(
        choices=NIVEL_CHOICES,
        verbose_name="Nível de Impacto Ambiental"
    )
    
    descricao_impacto = models.TextField(
        verbose_name="Descrição do Impacto",
        help_text="Descreva os impactos observados nos lençóis freáticos, rios e mares"
    )
    
    data_identificacao = models.DateField(
        default=timezone.now,
        verbose_name="Data de Identificação"
    )
    
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        verbose_name="Longitude"
    )
    
    usuario_cadastro = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Cadastrado por"
    )
    
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    
    ativo = models.BooleanField(default=True, verbose_name="Registro Ativo")

    def __str__(self):
        return f"{self.nome_propriedade} - {self.proprietario} (Nível {self.nivel_impacto})"

    class Meta:
        verbose_name = "Propriedade Rural"
        verbose_name_plural = "Propriedades Rurais"
        ordering = ['-data_cadastro']
