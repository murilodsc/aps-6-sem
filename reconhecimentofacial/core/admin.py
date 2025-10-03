from django.contrib import admin
from .models import FotoCapturada


@admin.register(FotoCapturada)
class FotoCapturadaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_captura', 'imagem')
    list_filter = ('data_captura',)
    search_fields = ('nome',)
    readonly_fields = ('data_captura',)
    ordering = ('-data_captura',)
