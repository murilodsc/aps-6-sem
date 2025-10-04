#!/bin/bash

# Script de Deploy Automático para EC2
# Execute no servidor EC2 após clonar o repositório

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do Sistema de Reconhecimento Facial..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="/home/ubuntu/APS6-2.0"
APP_DIR="$PROJECT_DIR/reconhecimentofacial"
VENV_DIR="$PROJECT_DIR/.venv"

# Função para imprimir mensagens coloridas
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar se está rodando como ubuntu
if [ "$USER" != "ubuntu" ]; then
    print_error "Este script deve ser executado como usuário 'ubuntu'"
    exit 1
fi

# 1. Atualizar código do repositório
print_message "Atualizando código do repositório..."
cd $PROJECT_DIR
if [ -d ".git" ]; then
    git pull
else
    print_warning "Não é um repositório git. Pulando atualização..."
fi

# 2. Ativar ambiente virtual
print_message "Ativando ambiente virtual..."
source $VENV_DIR/bin/activate

# 3. Atualizar dependências
print_message "Instalando/atualizando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn whitenoise python-decouple

# 4. Verificar se .env existe
if [ ! -f "$APP_DIR/.env" ]; then
    print_error "Arquivo .env não encontrado em $APP_DIR/"
    print_warning "Copie .env.example para .env e configure as variáveis:"
    print_warning "cp .env.example $APP_DIR/.env"
    exit 1
fi

# 5. Executar migrações
print_message "Executando migrações do banco de dados..."
cd $APP_DIR
python manage.py migrate --noinput

# 6. Coletar arquivos estáticos
print_message "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# 7. Criar diretório de mídia se não existir
print_message "Configurando diretório de mídia..."
mkdir -p $APP_DIR/media/fotos_capturadas
chmod -R 755 $APP_DIR/media

# 8. Reiniciar Gunicorn
print_message "Reiniciando serviço Gunicorn..."
sudo systemctl restart gunicorn
sleep 2

# 9. Verificar status do Gunicorn
if sudo systemctl is-active --quiet gunicorn; then
    print_message "✅ Gunicorn está rodando"
else
    print_error "❌ Gunicorn falhou ao iniciar"
    print_warning "Verificando logs..."
    sudo journalctl -u gunicorn -n 20
    exit 1
fi

# 10. Reiniciar Nginx
print_message "Reiniciando Nginx..."
sudo systemctl restart nginx

# 11. Verificar status do Nginx
if sudo systemctl is-active --quiet nginx; then
    print_message "✅ Nginx está rodando"
else
    print_error "❌ Nginx falhou ao iniciar"
    print_warning "Verificando logs..."
    sudo tail -n 20 /var/log/nginx/error.log
    exit 1
fi

# 12. Verificar permissões
print_message "Ajustando permissões..."
sudo chown -R ubuntu:www-data $APP_DIR/media
sudo chown -R ubuntu:www-data $APP_DIR/staticfiles
sudo chmod -R 755 $APP_DIR/media
sudo chmod -R 755 $APP_DIR/staticfiles

# 13. Limpar cache Python
print_message "Limpando cache Python..."
find $PROJECT_DIR -type d -name '__pycache__' -exec rm -r {} + 2>/dev/null || true
find $PROJECT_DIR -type f -name '*.pyc' -delete

print_message ""
print_message "=========================================="
print_message "✅ Deploy concluído com sucesso!"
print_message "=========================================="
print_message ""
print_message "📊 Status dos serviços:"
sudo systemctl status gunicorn --no-pager -l
sudo systemctl status nginx --no-pager -l
print_message ""
print_message "📝 Para ver os logs:"
print_message "  Gunicorn: sudo journalctl -u gunicorn -f"
print_message "  Nginx: sudo tail -f /var/log/nginx/error.log"
print_message ""
