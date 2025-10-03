from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


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
