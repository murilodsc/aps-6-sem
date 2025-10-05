# 📁 Deploy - Arquivos de Configuração

Este diretório contém **exemplos** de arquivos de configuração para deploy em produção.

## ⚠️ IMPORTANTE

**NÃO versione arquivos com configurações reais do servidor!**

- ❌ `nginx.conf` (configuração real)
- ❌ `gunicorn.service` (configuração real)
- ❌ Arquivos `.sock` (sockets)
- ✅ `*.example` (exemplos OK para versionar)

## 📋 Arquivos de Exemplo

### `examples/nginx.conf.example`
Configuração de exemplo do Nginx para servir a aplicação Django.

**Como usar:**
```bash
# No servidor EC2
sudo cp deploy/examples/nginx.conf.example /etc/nginx/sites-available/reconhecimento
sudo nano /etc/nginx/sites-available/reconhecimento
# Ajuste os caminhos marcados com "AJUSTAR:"

sudo ln -s /etc/nginx/sites-available/reconhecimento /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### `examples/gunicorn.service.example`
Configuração de exemplo do serviço systemd para Gunicorn.

**Como usar:**
```bash
# No servidor EC2
sudo cp deploy/examples/gunicorn.service.example /etc/systemd/system/gunicorn.service
sudo nano /etc/systemd/system/gunicorn.service
# Ajuste os caminhos marcados com "AJUSTAR:"

sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

## 📚 Documentação

Consulte [`DEPLOY_EC2.md`](../DEPLOY_EC2.md) para o guia completo de deploy.

## 🔒 Segurança

**Nunca commite:**
- Chaves privadas (`.pem`, `.key`)
- Arquivos `.env` com secrets reais
- Configurações com IPs/domínios reais do servidor
- Arquivos de banco de dados (`db.sqlite3`)
