# 🚀 Guia de Deploy no EC2 - Sistema de Reconhecimento Facial

## 📋 Pré-requisitos

- Instância EC2 criada e rodando (Ubuntu 22.04 LTS recomendado)
- Par de chaves SSH (.pem) para acesso
- Grupo de segurança configurado com portas abertas:
  - **22** (SSH)
  - **80** (HTTP)
  - **443** (HTTPS - opcional)
  - **8000** (Django temporário - para testes)

---

## 🔧 1. Preparar o Projeto Localmente

### 1.1 Criar arquivo `requirements.txt` completo

```bash
cd /Users/murilocabral/IdeaProjects/APS6-2.0
pip freeze > requirements.txt
```

### 1.2 Criar arquivo `.env.example` (modelo de variáveis de ambiente)

```bash
# .env.example
DEBUG=False
SECRET_KEY=sua-chave-secreta-aqui
ALLOWED_HOSTS=seu-ip-ec2.compute.amazonaws.com,seu-dominio.com
DATABASE_URL=sqlite:///db.sqlite3
```

### 1.3 Atualizar `settings.py` para produção

Adicione no topo do `settings.py`:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

### 1.4 Criar arquivo `.gitignore` (se não existe)

```gitignore
*.pyc
__pycache__/
db.sqlite3
.env
.venv/
venv/
media/
staticfiles/
*.log
.DS_Store
*.pem
```

---

## 🖥️ 2. Conectar ao EC2 e Configurar Servidor

### 2.1 Conectar via SSH

```bash
chmod 400 sua-chave.pem
ssh -i sua-chave.pem ubuntu@seu-ip-publico-ec2
```

### 2.2 Atualizar o sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Instalar dependências do sistema

```bash
# Python e ferramentas
sudo apt install -y python3.12 python3.12-venv python3-pip python3-dev

# Git
sudo apt install -y git

# Nginx (servidor web)
sudo apt install -y nginx

# Dependências para OpenCV e face_recognition
sudo apt install -y build-essential cmake
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libboost-all-dev
sudo apt install -y libsm6 libxext6 libxrender-dev libgomp1 libglib2.0-0

# Dependências para dlib (usado pelo face_recognition)
sudo apt install -y libopenblas-dev liblapack-dev
```

### 2.4 Instalar dlib (pode demorar 10-20 minutos)

```bash
pip3 install dlib
```

---

## 📦 3. Transferir o Projeto para o EC2

### Opção A: Via Git (Recomendado)

```bash
# No EC2
cd /home/ubuntu
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### Opção B: Via SCP (transferência direta)

```bash
# No seu Mac
scp -i sua-chave.pem -r /Users/murilocabral/IdeaProjects/APS6-2.0 ubuntu@seu-ip-ec2:/home/ubuntu/
```

---

## 🐍 4. Configurar Ambiente Python no EC2

### 4.1 Criar ambiente virtual

```bash
cd /home/ubuntu/APS6-2.0
python3.12 -m venv .venv
source .venv/bin/activate
```

### 4.2 Instalar dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Se houver problemas com face_recognition, instale manualmente:
pip install cmake
pip install dlib
pip install face-recognition
```

### 4.3 Instalar pacotes adicionais para produção

```bash
pip install gunicorn
pip install python-dotenv
pip install whitenoise  # Para servir arquivos estáticos
```

---

## ⚙️ 5. Configurar Django para Produção

### 5.1 Criar arquivo `.env`

```bash
cd /home/ubuntu/APS6-2.0/reconhecimentofacial
nano .env
```

Adicione:
```env
DEBUG=False
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=seu-ip-ec2,seu-dominio.com
```

### 5.2 Atualizar `settings.py` para servir arquivos estáticos

Adicione no final do `settings.py`:

```python
# Whitenoise para servir arquivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Arquivos estáticos
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configurações de segurança para produção
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
```

### 5.3 Coletar arquivos estáticos

```bash
cd /home/ubuntu/APS6-2.0/reconhecimentofacial
source ../.venv/bin/activate
python manage.py collectstatic --noinput
```

### 5.4 Executar migrações

```bash
python manage.py migrate
```

### 5.5 Criar superusuário

```bash
python manage.py createsuperuser
```

---

## 🚀 6. Configurar Gunicorn (WSGI Server)

### 6.1 Testar Gunicorn

```bash
cd /home/ubuntu/APS6-2.0/reconhecimentofacial
source ../.venv/bin/activate
gunicorn --bind 0.0.0.0:8000 reconhecimentofacial.wsgi:application
```

Acesse: `http://seu-ip-ec2:8000`

### 6.2 Criar arquivo de serviço systemd

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Adicione:

```ini
[Unit]
Description=Gunicorn daemon for Django Reconhecimento Facial
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/APS6-2.0/reconhecimentofacial
Environment="PATH=/home/ubuntu/APS6-2.0/.venv/bin"
ExecStart=/home/ubuntu/APS6-2.0/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/ubuntu/APS6-2.0/reconhecimentofacial/gunicorn.sock \
    reconhecimentofacial.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 6.3 Iniciar e habilitar o serviço

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

## 🌐 7. Configurar Nginx

### 7.1 Criar configuração do site

```bash
sudo nano /etc/nginx/sites-available/reconhecimento
```

Adicione:

```nginx
server {
    listen 80;
    server_name seu-ip-ec2 seu-dominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Arquivos estáticos
    location /static/ {
        alias /home/ubuntu/APS6-2.0/reconhecimentofacial/staticfiles/;
    }
    
    # Arquivos de mídia (fotos capturadas)
    location /media/ {
        alias /home/ubuntu/APS6-2.0/reconhecimentofacial/media/;
    }
    
    # Proxy para Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/APS6-2.0/reconhecimentofacial/gunicorn.sock;
        
        # Timeout maior para reconhecimento facial
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Aumentar tamanho máximo de upload (para fotos)
    client_max_body_size 10M;
}
```

### 7.2 Ativar o site

```bash
sudo ln -s /etc/nginx/sites-available/reconhecimento /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7.3 Ajustar permissões

```bash
sudo usermod -a -G ubuntu www-data
sudo chmod 710 /home/ubuntu
sudo chmod -R 755 /home/ubuntu/APS6-2.0/reconhecimentofacial/media
sudo chmod -R 755 /home/ubuntu/APS6-2.0/reconhecimentofacial/staticfiles
```

---

## 🔒 8. Configurar SSL/HTTPS (Opcional mas Recomendado)

### 8.1 Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.2 Obter certificado SSL

```bash
sudo certbot --nginx -d seu-dominio.com
```

### 8.3 Renovação automática

```bash
sudo systemctl status certbot.timer
```

---

## 📸 9. Configurar Câmera/Reconhecimento Facial

### 9.1 Verificar permissões de câmera

O reconhecimento facial usa a câmera do **cliente** (navegador), então não há configuração especial no servidor.

### 9.2 HTTPS obrigatório para câmera

**IMPORTANTE**: Navegadores modernos exigem HTTPS para acessar a câmera. Configure o SSL (passo 8) ou use:

```bash
# Para testes, você pode usar o IP com HTTP, mas em produção use HTTPS
```

---

## 🔄 10. Comandos Úteis de Manutenção

### Reiniciar serviços após mudanças no código

```bash
# Atualizar código
cd /home/ubuntu/APS6-2.0
git pull

# Ativar ambiente virtual
source .venv/bin/activate
cd reconhecimentofacial

# Coletar estáticos
python manage.py collectstatic --noinput

# Migrar banco
python manage.py migrate

# Reiniciar Gunicorn
sudo systemctl restart gunicorn

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Ver logs

```bash
# Logs do Gunicorn
sudo journalctl -u gunicorn -f

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Logs do Django (se configurado)
tail -f /home/ubuntu/APS6-2.0/reconhecimentofacial/logs/django.log
```

### Monitorar recursos

```bash
# CPU e memória
htop

# Espaço em disco
df -h

# Processos do Gunicorn
ps aux | grep gunicorn
```

---

## 🛡️ 11. Segurança Adicional

### 11.1 Configurar Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 11.2 Desabilitar acesso root SSH

```bash
sudo nano /etc/ssh/sshd_config
# Altere: PermitRootLogin no
sudo systemctl restart sshd
```

### 11.3 Instalar Fail2Ban

```bash
sudo apt install -y fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

## ✅ 12. Checklist Final

- [ ] EC2 rodando e acessível via SSH
- [ ] Dependências do sistema instaladas (Python, Nginx, OpenCV, dlib)
- [ ] Código transferido para EC2
- [ ] Ambiente virtual criado e dependências instaladas
- [ ] `.env` configurado com `DEBUG=False`
- [ ] `ALLOWED_HOSTS` configurado no settings.py
- [ ] Migrações executadas
- [ ] Superusuário criado
- [ ] Arquivos estáticos coletados
- [ ] Gunicorn configurado e rodando
- [ ] Nginx configurado e rodando
- [ ] Site acessível via HTTP (porta 80)
- [ ] SSL configurado (HTTPS) - necessário para câmera
- [ ] Firewall configurado
- [ ] Testes de reconhecimento facial funcionando

---

## 🐛 13. Troubleshooting

### Problema: "Bad Gateway 502"
```bash
# Verificar status do Gunicorn
sudo systemctl status gunicorn

# Ver logs
sudo journalctl -u gunicorn -n 50
```

### Problema: Arquivos estáticos não carregam
```bash
# Coletar novamente
python manage.py collectstatic --noinput

# Verificar permissões
ls -la /home/ubuntu/APS6-2.0/reconhecimentofacial/staticfiles
```

### Problema: Câmera não funciona
- Verifique se está usando HTTPS (obrigatório para câmera)
- Teste em navegador diferente
- Verifique console do navegador (F12)

### Problema: face_recognition não instala
```bash
# Instalar dependências manualmente
sudo apt install -y cmake libopenblas-dev liblapack-dev
pip install cmake
pip install dlib
pip install face-recognition
```

---

## 📞 Contato e Suporte

- **Logs do sistema**: `/var/log/nginx/` e `journalctl`
- **Documentação Django**: https://docs.djangoproject.com/
- **AWS EC2**: https://docs.aws.amazon.com/ec2/

---

**Última atualização**: 04 de outubro de 2025
