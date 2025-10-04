# 🚀 Guia Rápido de Deploy EC2

## 📋 Checklist Pré-Deploy (No seu Mac)

```bash
# 1. Verificar se está no branch correto
cd /Users/murilocabral/IdeaProjects/APS6-2.0
git status

# 2. Commitar mudanças pendentes
git add .
git commit -m "Preparar para deploy em produção"
git push origin feature/reconhecimento

# 3. Gerar requirements.txt
source .venv/bin/activate
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Atualizar requirements.txt"
git push
```

---

## 🔌 Conectar ao EC2

```bash
# Ajustar permissões da chave (só precisa fazer uma vez)
chmod 400 ~/Downloads/sua-chave-ec2.pem

# Conectar via SSH
ssh -i ~/Downloads/sua-chave-ec2.pem ubuntu@SEU-IP-EC2
```

**Substitua:**
- `~/Downloads/sua-chave-ec2.pem` pelo caminho da sua chave
- `SEU-IP-EC2` pelo IP público da sua instância

---

## ⚙️ Instalação Inicial (Execute apenas uma vez)

### 1. Atualizar sistema e instalar dependências

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Python e ferramentas básicas
sudo apt install -y python3.12 python3.12-venv python3-pip git nginx

# Dependências para OpenCV e face_recognition
sudo apt install -y build-essential cmake
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libboost-all-dev libsm6 libxext6 libxrender-dev libgomp1 libglib2.0-0
sudo apt install -y libopenblas-dev liblapack-dev
```

### 2. Clonar o repositório

```bash
cd ~
git clone https://github.com/murilodsc/aps-6-sem.git APS6-2.0
cd APS6-2.0
git checkout feature/reconhecimento
```

### 3. Criar e ativar ambiente virtual

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar dependências Python (pode demorar!)

```bash
# Instalar pip atualizado
pip install --upgrade pip

# Instalar dependências do projeto
pip install -r requirements.txt

# Instalar pacotes de produção
pip install gunicorn whitenoise python-decouple
```

### 5. Configurar variáveis de ambiente

```bash
cd reconhecimentofacial

# Criar arquivo .env
nano .env
```

Cole o seguinte conteúdo (ajuste os valores):

```env
DEBUG=False
SECRET_KEY=GERE-UMA-CHAVE-SUPER-SECRETA-AQUI-COM-PELO-MENOS-50-CARACTERES-ALEATORIOS
ALLOWED_HOSTS=SEU-IP-EC2,seu-dominio.com
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
```

**Para gerar SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Salvar: `Ctrl+O`, Enter, `Ctrl+X`

### 6. Configurar banco de dados

```bash
# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar diretório de logs
mkdir -p ~/APS6-2.0/logs
```

### 7. Configurar Gunicorn

```bash
# Copiar arquivo de serviço
sudo cp ~/APS6-2.0/gunicorn.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Iniciar Gunicorn
sudo systemctl start gunicorn

# Habilitar para iniciar com o sistema
sudo systemctl enable gunicorn

# Verificar status
sudo systemctl status gunicorn
```

### 8. Configurar Nginx

```bash
# Copiar arquivo de configuração
sudo cp ~/APS6-2.0/nginx.conf /etc/nginx/sites-available/reconhecimento

# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/reconhecimento /etc/nginx/sites-enabled/

# Remover configuração padrão
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 9. Ajustar permissões

```bash
sudo usermod -a -G ubuntu www-data
sudo chmod 710 /home/ubuntu
sudo chmod -R 755 ~/APS6-2.0/reconhecimentofacial/media
sudo chmod -R 755 ~/APS6-2.0/reconhecimentofacial/staticfiles
```

### 10. Configurar Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

---

## 🔄 Deploy de Atualizações (Execute quando fizer mudanças)

```bash
# Conectar ao EC2
ssh -i ~/Downloads/sua-chave-ec2.pem ubuntu@SEU-IP-EC2

# Executar script de deploy
cd ~/APS6-2.0
chmod +x deploy.sh
./deploy.sh
```

**OU manualmente:**

```bash
cd ~/APS6-2.0
source .venv/bin/activate

# Atualizar código
git pull

# Instalar novas dependências
pip install -r requirements.txt

# Migrar banco
cd reconhecimentofacial
python manage.py migrate

# Coletar estáticos
python manage.py collectstatic --noinput

# Reiniciar serviços
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 📊 Comandos Úteis

### Ver logs em tempo real

```bash
# Logs do Gunicorn
sudo journalctl -u gunicorn -f

# Logs do Nginx (erros)
sudo tail -f /var/log/nginx/reconhecimento-error.log

# Logs do Nginx (acesso)
sudo tail -f /var/log/nginx/reconhecimento-access.log
```

### Verificar status dos serviços

```bash
# Gunicorn
sudo systemctl status gunicorn

# Nginx
sudo systemctl status nginx

# Ver processos
ps aux | grep gunicorn
```

### Reiniciar serviços

```bash
# Gunicorn
sudo systemctl restart gunicorn

# Nginx
sudo systemctl restart nginx

# Ambos
sudo systemctl restart gunicorn nginx
```

### Monitorar recursos

```bash
# CPU e memória
htop

# Espaço em disco
df -h

# Uso de rede
sudo iftop
```

---

## 🔒 Configurar HTTPS (Opcional mas Recomendado)

### Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Obter certificado SSL

```bash
sudo certbot --nginx -d seu-dominio.com
```

### Renovação automática

```bash
# Testar renovação
sudo certbot renew --dry-run

# Verificar timer de renovação
sudo systemctl status certbot.timer
```

---

## 🐛 Troubleshooting

### Erro 502 Bad Gateway

```bash
# Verificar Gunicorn
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -n 50

# Verificar socket
ls -la /home/ubuntu/APS6-2.0/reconhecimentofacial/gunicorn.sock
```

### Arquivos estáticos não carregam

```bash
cd ~/APS6-2.0/reconhecimentofacial
source ../.venv/bin/activate
python manage.py collectstatic --noinput

# Verificar permissões
ls -la staticfiles/
```

### Câmera não funciona

- ✅ Certifique-se de que está usando HTTPS (obrigatório para câmera)
- ✅ Configure SSL com Certbot
- ✅ Teste em navegadores diferentes (Chrome, Firefox)

### face_recognition não instala

```bash
# Instalar dependências
sudo apt install -y cmake libopenblas-dev liblapack-dev

# Instalar no venv
source .venv/bin/activate
pip install cmake
pip install dlib
pip install face-recognition
```

---

## 📝 Informações Importantes

### URLs do Sistema

- **HTTP**: `http://SEU-IP-EC2`
- **HTTPS**: `https://seu-dominio.com` (após configurar SSL)
- **Admin**: `http://SEU-IP-EC2/admin/`

### Credenciais

- **Superusuário**: Criado no passo 6 da instalação
- **Acesso SSH**: Chave .pem fornecida pela AWS

### Backup

```bash
# Backup do banco de dados
cp ~/APS6-2.0/reconhecimentofacial/db.sqlite3 ~/backup-$(date +%Y%m%d).sqlite3

# Backup das fotos
tar -czf ~/fotos-backup-$(date +%Y%m%d).tar.gz ~/APS6-2.0/reconhecimentofacial/media/
```

---

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs primeiro
2. Consulte o arquivo `DEPLOY_EC2.md` para detalhes completos
3. Revise as configurações do grupo de segurança no AWS Console

---

**Última atualização**: 04 de outubro de 2025
