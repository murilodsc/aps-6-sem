from django.contrib import admin
from django.utils.html import format_html
from .models import PropriedadeRural, PerfilUsuario


@admin.register(PropriedadeRural)
class PropriedadeRuralAdmin(admin.ModelAdmin):
    list_display = ('nome_propriedade', 'proprietario', 'cidade', 'estado', 'nivel_impacto', 'agrotoxico_utilizado', 'data_identificacao', 'ativo')
    list_filter = ('nivel_impacto', 'estado', 'ativo', 'data_identificacao')
    search_fields = ('nome_propriedade', 'proprietario', 'cidade', 'agrotoxico_utilizado', 'cpf_cnpj')
    readonly_fields = ('data_cadastro', 'data_atualizacao', 'usuario_cadastro')
    ordering = ('-data_cadastro',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_propriedade', 'proprietario', 'cpf_cnpj', 'area_hectares')
        }),
        ('Localização', {
            'fields': ('endereco', 'cidade', 'estado', 'latitude', 'longitude')
        }),
        ('Agrotóxicos e Impacto', {
            'fields': ('agrotoxico_utilizado', 'nivel_impacto', 'descricao_impacto', 'data_identificacao')
        }),
        ('Metadados', {
            'fields': ('usuario_cadastro', 'data_cadastro', 'data_atualizacao', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se está criando um novo objeto
            obj.usuario_cadastro = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('get_nome_completo', 'get_username', 'get_email', 'telefone', 'foto_thumbnail', 'data_cadastro')
    list_filter = ('data_cadastro',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'telefone')
    readonly_fields = ('foto_thumbnail', 'data_cadastro')
    ordering = ('-data_cadastro',)
    
    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user', 'telefone', 'data_nascimento', 'bio')
        }),
        ('Foto', {
            'fields': ('foto', 'foto_thumbnail')
        }),
        ('Metadados', {
            'fields': ('data_cadastro',),
            'classes': ('collapse',)
        }),
    )
    
    def get_nome_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    get_nome_completo.short_description = 'Nome'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def foto_thumbnail(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="80" height="80" style="border-radius: 50%; object-fit: cover;" />', obj.foto.url)
        return format_html('<div style="width: 80px; height: 80px; border-radius: 50%; background: #ccc; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">Sem Foto</div>')
    foto_thumbnail.short_description = 'Foto'

