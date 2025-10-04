#!/bin/bash

# Script de Verificação Pré-Deploy
# Execute este script no seu Mac ANTES de fazer o deploy

echo "======================================"
echo "🔍 VERIFICAÇÃO PRÉ-DEPLOY"
echo "======================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de erros
ERRORS=0
WARNINGS=0

# 1. Verificar se está no diretório correto
echo "1. Verificando diretório..."
if [ -f "manage.py" ] || [ -d "reconhecimentofacial" ]; then
    echo -e "${GREEN}✓${NC} Diretório correto"
else
    echo -e "${RED}✗${NC} Execute este script na raiz do projeto"
    ERRORS=$((ERRORS + 1))
fi

# 2. Verificar se .env.example existe
echo "2. Verificando .env.example..."
if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓${NC} .env.example encontrado"
else
    echo -e "${YELLOW}!${NC} .env.example não encontrado"
    WARNINGS=$((WARNINGS + 1))
fi

# 3. Verificar requirements.txt
echo "3. Verificando requirements.txt..."
if [ -f "requirements.txt" ]; then
    LINE_COUNT=$(wc -l < requirements.txt)
    if [ $LINE_COUNT -gt 5 ]; then
        echo -e "${GREEN}✓${NC} requirements.txt existe ($LINE_COUNT pacotes)"
    else
        echo -e "${YELLOW}!${NC} requirements.txt parece vazio ou incompleto"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}✗${NC} requirements.txt não encontrado"
    echo "   Execute: pip freeze > requirements.txt"
    ERRORS=$((ERRORS + 1))
fi

# 4. Verificar arquivos de configuração de deploy
echo "4. Verificando arquivos de deploy..."
DEPLOY_FILES=("DEPLOY_EC2.md" "DEPLOY_QUICK_START.md" "deploy.sh" "gunicorn.service" "nginx.conf")
for file in "${DEPLOY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
    else
        echo -e "   ${YELLOW}!${NC} $file não encontrado"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# 5. Verificar se Git está configurado
echo "5. Verificando Git..."
if [ -d ".git" ]; then
    echo -e "${GREEN}✓${NC} Repositório Git inicializado"
    
    # Verificar branch
    BRANCH=$(git branch --show-current)
    echo "   Branch atual: $BRANCH"
    
    # Verificar mudanças não commitadas
    if git diff-index --quiet HEAD --; then
        echo -e "${GREEN}✓${NC} Sem mudanças pendentes"
    else
        echo -e "${YELLOW}!${NC} Existem mudanças não commitadas"
        echo "   Execute: git add . && git commit -m 'Preparar deploy'"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}!${NC} Não é um repositório Git"
    WARNINGS=$((WARNINGS + 1))
fi

# 6. Verificar estrutura do projeto Django
echo "6. Verificando estrutura Django..."
if [ -f "reconhecimentofacial/manage.py" ]; then
    echo -e "${GREEN}✓${NC} manage.py encontrado"
else
    echo -e "${RED}✗${NC} manage.py não encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "reconhecimentofacial/reconhecimentofacial/settings.py" ]; then
    echo -e "${GREEN}✓${NC} settings.py encontrado"
    
    # Verificar se python-decouple está configurado
    if grep -q "from decouple import config" "reconhecimentofacial/reconhecimentofacial/settings.py"; then
        echo -e "${GREEN}✓${NC} python-decouple configurado"
    else
        echo -e "${YELLOW}!${NC} python-decouple não detectado em settings.py"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}✗${NC} settings.py não encontrado"
    ERRORS=$((ERRORS + 1))
fi

# 7. Verificar dependências principais
echo "7. Verificando dependências principais..."
REQUIRED_PACKAGES=("Django" "opencv-python" "face-recognition" "python-decouple")
if [ -f "requirements.txt" ]; then
    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        if grep -qi "$pkg" requirements.txt; then
            echo -e "   ${GREEN}✓${NC} $pkg"
        else
            echo -e "   ${RED}✗${NC} $pkg não encontrado em requirements.txt"
            ERRORS=$((ERRORS + 1))
        fi
    done
fi

# 8. Verificar se deploy.sh tem permissão de execução
echo "8. Verificando permissões..."
if [ -f "deploy.sh" ]; then
    if [ -x "deploy.sh" ]; then
        echo -e "${GREEN}✓${NC} deploy.sh é executável"
    else
        echo -e "${YELLOW}!${NC} deploy.sh precisa de permissão de execução"
        echo "   Execute: chmod +x deploy.sh"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Resumo
echo ""
echo "======================================"
echo "📊 RESUMO"
echo "======================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 TUDO PRONTO PARA DEPLOY!${NC}"
    echo ""
    echo "Próximos passos:"
    echo "1. Faça commit das mudanças: git add . && git commit -m 'Deploy'"
    echo "2. Faça push: git push origin $(git branch --show-current)"
    echo "3. Conecte ao EC2: ssh -i sua-chave.pem ubuntu@SEU-IP-EC2"
    echo "4. Siga o guia: DEPLOY_QUICK_START.md"
else
    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}❌ $ERRORS erro(s) encontrado(s)${NC}"
        echo "Corrija os erros antes de fazer o deploy."
    fi
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS aviso(s)${NC}"
        echo "Resolva os avisos antes de prosseguir."
    fi
fi

echo ""
echo "📚 Documentação:"
echo "   - Guia completo: DEPLOY_EC2.md"
echo "   - Guia rápido: DEPLOY_QUICK_START.md"
echo "   - Resumo: DEPLOY_RESUMO.md"
echo ""
