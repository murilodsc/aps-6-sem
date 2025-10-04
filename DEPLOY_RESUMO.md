# 🎯 Resumo Executivo - Deploy EC2

## 📂 Arquivos Criados para Deploy

✅ **DEPLOY_EC2.md** - Guia completo e detalhado de deploy (passo a passo completo)
✅ **DEPLOY_QUICK_START.md** - Guia rápido com comandos essenciais
✅ **deploy.sh** - Script automatizado de deploy
✅ **gunicorn.service** - Arquivo de serviço systemd
✅ **nginx.conf** - Configuração do Nginx
✅ **.env.example** - Template de variáveis de ambiente
✅ **.gitignore** - Atualizado com exclusões para AWS
✅ **requirements.txt** - Dependências Python atualizadas
✅ **settings.py** - Configurado com segurança para produção

---

## 🚀 Ordem de Execução no EC2

### 1️⃣ **Primeira Vez (Instalação Inicial)**

Siga o arquivo **DEPLOY_QUICK_START.md** na ordem:

1. Conectar ao EC2 via SSH
2. Instalar dependências do sistema
3. Clonar repositório
4. Criar ambiente virtual
5. Instalar dependências Python
6. Configurar .env
7. Executar migrações
8. Configurar Gunicorn
9. Configurar Nginx
10. Ajustar permissões
11. Configurar firewall

**Tempo estimado:** 30-45 minutos

### 2️⃣ **Atualizações Futuras**

```bash
cd ~/APS6-2.0
chmod +x deploy.sh
./deploy.sh
```

**Tempo:** 2-3 minutos

---

## 📋 Checklist Antes de Fazer o Deploy

### No seu Mac (antes de ir pro EC2):

- [ ] Código está funcionando localmente
- [ ] Executar: `git add . && git commit -m "Deploy para produção"`
- [ ] Executar: `git push origin feature/reconhecimento`
- [ ] Verificar que `requirements.txt` está atualizado (✅ já foi gerado)

### Informações que você vai precisar:

- [ ] **IP público da instância EC2** - Pegar no AWS Console
- [ ] **Arquivo .pem** - Chave SSH para conectar (salva no Downloads)
- [ ] **Porta 22 liberada** - Para SSH
- [ ] **Portas 80 e 443 liberadas** - Para HTTP/HTTPS

---

## ⚠️ IMPORTANTE: Reconhecimento Facial em Produção

### 🔒 HTTPS é OBRIGATÓRIO

Navegadores modernos **exigem HTTPS** para acessar a câmera. Você tem 3 opções:

#### Opção 1: Usar IP temporariamente (apenas para testes)
- Alguns navegadores permitem câmera via HTTP no IP local
- **Não recomendado para produção**

#### Opção 2: Configurar SSL com Let's Encrypt (RECOMENDADO)
```bash
# Depois de tudo configurado
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

#### Opção 3: Usar CloudFront da AWS
- Configurar CloudFront na frente do EC2
- CloudFront fornece SSL automaticamente

---

## 🔧 Variáveis de Ambiente (.env)

Criar o arquivo `/home/ubuntu/APS6-2.0/reconhecimentofacial/.env`:

```env
DEBUG=False
SECRET_KEY=GERAR-CHAVE-SECRETA-AQUI
ALLOWED_HOSTS=SEU-IP-EC2,seu-dominio.com
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
```

**Para gerar a SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## 📊 Monitoramento após Deploy

### Verificar se está tudo rodando:

```bash
# Status dos serviços
sudo systemctl status gunicorn
sudo systemctl status nginx

# Ver logs em tempo real
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
```

### Testar o site:

1. **HTTP**: `http://SEU-IP-EC2`
2. **Admin**: `http://SEU-IP-EC2/admin/`
3. **Login Facial**: `http://SEU-IP-EC2/login/facial/`

---

## 🐛 Problemas Comuns e Soluções

### Erro 502 Bad Gateway
```bash
sudo systemctl restart gunicorn
sudo journalctl -u gunicorn -n 50
```

### Arquivos estáticos não carregam
```bash
cd ~/APS6-2.0/reconhecimentofacial
source ../.venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

### Câmera não funciona
- Configure HTTPS com Let's Encrypt
- Ou use domínio com SSL da AWS

### face_recognition demora muito para instalar
- É normal! O dlib pode demorar 10-20 minutos para compilar
- Aguarde e tome um café ☕

---

## 📞 Comandos Úteis

### Conectar ao EC2
```bash
ssh -i ~/Downloads/sua-chave.pem ubuntu@SEU-IP-EC2
```

### Atualizar código
```bash
cd ~/APS6-2.0
git pull
./deploy.sh
```

### Reiniciar tudo
```bash
sudo systemctl restart gunicorn nginx
```

### Ver uso de recursos
```bash
htop          # CPU e memória
df -h         # Espaço em disco
sudo ufw status  # Firewall
```

---

## ✅ Teste Final

Após deploy completo, teste:

1. [ ] Site carrega na home
2. [ ] Login normal funciona
3. [ ] Admin funciona
4. [ ] Páginas de usuários funcionam
5. [ ] Páginas de propriedades funcionam
6. [ ] Arquivos estáticos carregam (CSS/JS)
7. [ ] Fotos de perfil aparecem
8. [ ] Sistema de permissões funciona
9. [ ] Login facial funciona (se HTTPS configurado)

---

## 🎉 Próximos Passos Recomendados

1. **Configurar HTTPS** - Usar Let's Encrypt
2. **Configurar backup automático** - Banco de dados e fotos
3. **Monitoramento** - Usar CloudWatch da AWS
4. **Domínio personalizado** - Registrar um domínio
5. **Email** - Configurar SMTP para recuperação de senha

---

**Documentação completa em:** `DEPLOY_EC2.md`
**Comandos rápidos em:** `DEPLOY_QUICK_START.md`
**Script automatizado:** `./deploy.sh`

**Boa sorte com o deploy! 🚀**
