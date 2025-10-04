# 🔐 Sistema de Controle de Permissões para Criação de Usuários

## 📋 Resumo da Implementação

Sistema de permissões baseado em perfis que controla quem pode criar novos usuários e quais tipos de perfil podem ser atribuídos.

---

## 👥 Hierarquia de Perfis

### 1. **🎖️ Ministro do Meio Ambiente**
- **Pode criar:**
  - ✅ Ministros do Meio Ambiente
  - ✅ Diretores de Divisões
  - ✅ Usuários Comuns
- **Permissões:** Acesso total à criação de todos os tipos de perfil

### 2. **👔 Diretor de Divisões**
- **Pode criar:**
  - ✅ Diretores de Divisões
  - ✅ Usuários Comuns
- **Limitação:** ❌ Não pode criar Ministros

### 3. **👤 Usuário Comum**
- **Pode criar:**
  - ❌ Não pode criar nenhum usuário
- **Acesso:** Apenas auto-cadastro via página de registro

### 4. **⚙️ Admin/Superuser (Django)**
- **Pode criar:**
  - ✅ Todos os tipos de perfil
  - ✅ Acesso total ao sistema
- **Especial:** Acesso via Django Admin também

---

## 🛠️ Implementação Técnica

### **Funções Auxiliares** (`views.py`)

#### 1. `pode_criar_usuarios(usuario)`
Verifica se um usuário tem permissão para criar outros usuários.

```python
def pode_criar_usuarios(usuario):
    """Verifica se o usuário tem permissão para criar outros usuários"""
    if not usuario.is_authenticated:
        return False
    
    # Admin pode criar qualquer tipo
    if usuario.is_staff or usuario.is_superuser:
        return True
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return False
    
    # Ministro e Diretor podem criar usuários
    return usuario.perfil.tipo_perfil in ['MINISTRO', 'DIRETOR']
```

**Retorna:**
- `True`: Se o usuário pode criar outros usuários
- `False`: Se o usuário não tem permissão

---

#### 2. `obter_perfis_permitidos(usuario)`
Retorna lista de tipos de perfil que o usuário pode criar.

```python
def obter_perfis_permitidos(usuario):
    """
    Retorna lista de tipos de perfil que o usuário pode criar.
    Retorna tuplas (valor, label) para usar em select.
    """
    # Admin/Superuser: todos os perfis
    if usuario.is_staff or usuario.is_superuser:
        return [
            ('COMUM', '👤 Usuário Comum'),
            ('DIRETOR', '👔 Diretor de Divisões'),
            ('MINISTRO', '🎖️ Ministro do Meio Ambiente'),
        ]
    
    # Ministro: todos os perfis
    if usuario.perfil.tipo_perfil == 'MINISTRO':
        return [
            ('COMUM', '👤 Usuário Comum'),
            ('DIRETOR', '👔 Diretor de Divisões'),
            ('MINISTRO', '🎖️ Ministro do Meio Ambiente'),
        ]
    
    # Diretor: apenas Diretor e Comum
    if usuario.perfil.tipo_perfil == 'DIRETOR':
        return [
            ('COMUM', '👤 Usuário Comum'),
            ('DIRETOR', '👔 Diretor de Divisões'),
        ]
    
    # Usuário comum: nenhum
    return []
```

**Retorna:**
- Lista de tuplas `(valor, label)` com os perfis permitidos
- Lista vazia se não tiver permissão

---

### **View `usuario_create`**

Modificada para suportar dois modos de operação:

#### **Modo 1: Auto-cadastro (Usuário não logado)**
```python
# Sempre cria como Usuário Comum
perfil.tipo_perfil = 'COMUM'

# Faz login automático após cadastro
user_authenticated = authenticate(username=username, password=password)
if user_authenticated:
    login(request, user_authenticated)
    return redirect('index')
```

#### **Modo 2: Criação Administrativa (Usuário logado com permissão)**
```python
# Verifica permissão
is_admin_creating = request.user.is_authenticated and pode_criar_usuarios(request.user)

# Obtém perfis permitidos
perfis_permitidos = obter_perfis_permitidos(request.user)

# Valida tipo de perfil escolhido
tipo_perfil_escolhido = request.POST.get('tipo_perfil', 'COMUM')
perfis_valores = [p[0] for p in perfis_permitidos]

if tipo_perfil_escolhido in perfis_valores:
    perfil.tipo_perfil = tipo_perfil_escolhido
else:
    perfil.tipo_perfil = 'COMUM'
    messages.warning(request, 'Tipo de perfil inválido. Definido como Usuário Comum.')

# Redireciona para lista de usuários
return redirect('usuarios_list')
```

---

### **Template `usuario_form.html`**

Três cenários diferentes no formulário:

#### **Cenário 1: Auto-cadastro (não logado)**
```django
<!-- Campo oculto: sempre COMUM -->
<input type="hidden" name="tipo_perfil" value="COMUM" />

<!-- Mensagem informativa -->
<div class="info-box">
  <p>🎯 <strong>Seu perfil inicial:</strong> Usuário Comum</p>
  <small>Você será cadastrado como Usuário Comum...</small>
</div>
```

#### **Cenário 2: Admin/Ministro/Diretor criando usuário**
```django
{% elif is_admin_creating and perfis_permitidos %}
<div class="form-group">
  <label for="tipo_perfil">Tipo de Perfil *</label>
  <select id="tipo_perfil" name="tipo_perfil" required>
    {% for valor, label in perfis_permitidos %}
    <option value="{{ valor }}">{{ label }}</option>
    {% endfor %}
  </select>
  <small>Selecione o tipo de perfil para o novo usuário</small>
</div>
{% endif %}
```

#### **Cenário 3: Editando próprio perfil**
```django
<!-- Campo somente leitura -->
<input type="text" value="{{ usuario_perfil.perfil.get_tipo_perfil_display }}" readonly disabled />
<small>Apenas administradores podem alterar o tipo de perfil</small>
```

---

### **Template `usuarios_list.html`**

Botão "Novo Usuário" condicional:

```django
<div class="page-header">
  <h1>👥 Usuários do Sistema</h1>
  {% if pode_criar %}
  <a href="{% url 'usuario_create' %}" class="btn-primary">
    + Novo Usuário
  </a>
  {% endif %}
</div>
```

---

## 🔄 Fluxos de Uso

### **Fluxo 1: Auto-cadastro (Página de Login)**
1. Usuário não logado clica em "Cadastre-se aqui"
2. Preenche formulário (sem opção de escolher tipo de perfil)
3. Sistema cria usuário como "Usuário Comum" automaticamente
4. Faz login automático
5. Redireciona para página inicial

### **Fluxo 2: Ministro cria novo Diretor**
1. Ministro faz login
2. Acessa "Usuários" → "Novo Usuário"
3. Preenche formulário
4. Seleciona "Diretor de Divisões" no campo tipo de perfil
5. Sistema valida permissão
6. Cria usuário como Diretor
7. Redireciona para lista de usuários

### **Fluxo 3: Diretor tenta criar Ministro**
1. Diretor faz login
2. Acessa "Usuários" → "Novo Usuário"
3. Preenche formulário
4. Campo "Tipo de Perfil" mostra apenas:
   - Usuário Comum
   - Diretor de Divisões
5. ❌ Opção "Ministro" não aparece (permissão negada)

### **Fluxo 4: Usuário Comum tenta criar usuário**
1. Usuário Comum faz login
2. Acessa "Usuários"
3. ❌ Botão "Novo Usuário" não aparece
4. Pode apenas visualizar lista

---

## ✅ Validações Implementadas

### **1. Validação de Permissão**
```python
is_admin_creating = request.user.is_authenticated and pode_criar_usuarios(request.user)
```

### **2. Validação de Tipo de Perfil**
```python
perfis_valores = [p[0] for p in perfis_permitidos]
if tipo_perfil_escolhido in perfis_valores:
    perfil.tipo_perfil = tipo_perfil_escolhido
else:
    perfil.tipo_perfil = 'COMUM'
    messages.warning(request, 'Tipo de perfil inválido.')
```

### **3. Validação de Interface**
- Botão "Novo Usuário" só aparece se `pode_criar = True`
- Select de tipo de perfil só mostra opções permitidas
- Auto-cadastro sempre força perfil "COMUM"

---

## 🎯 Casos de Teste

### **Teste 1: Auto-cadastro**
- ✅ Deve criar usuário como "Comum"
- ✅ Deve fazer login automático
- ✅ Deve redirecionar para index

### **Teste 2: Ministro cria Ministro**
- ✅ Deve ver opção "Ministro" no select
- ✅ Deve criar usuário como "Ministro"
- ✅ Deve redirecionar para lista

### **Teste 3: Diretor cria Ministro**
- ✅ Não deve ver opção "Ministro" no select
- ✅ Se tentar forçar via POST, sistema força "Comum"

### **Teste 4: Usuário Comum acessa /usuario/create/**
- ✅ Deve ver formulário de auto-cadastro
- ✅ Não deve ter opção de escolher tipo de perfil

### **Teste 5: Usuário Comum acessa lista de usuários**
- ✅ Deve ver lista
- ✅ Não deve ver botão "Novo Usuário"

---

## 🔒 Segurança

### **Proteções Implementadas:**

1. **Validação Backend**: Mesmo que o frontend seja burlado, o backend valida permissões
2. **Lista Branca**: Sistema só aceita perfis da lista permitida para aquele usuário
3. **Fallback Seguro**: Em caso de erro, sempre cria como "Comum"
4. **Autenticação**: Todas as operações verificam se usuário está logado
5. **Perfil Obrigatório**: Sistema verifica `hasattr(usuario, 'perfil')` antes de acessar

---

## 📊 Matriz de Permissões

| Criador / Tipo Criado | Comum | Diretor | Ministro |
|------------------------|-------|---------|----------|
| **Auto-cadastro**      | ✅    | ❌      | ❌       |
| **Usuário Comum**      | ❌    | ❌      | ❌       |
| **Diretor**            | ✅    | ✅      | ❌       |
| **Ministro**           | ✅    | ✅      | ✅       |
| **Admin/Superuser**    | ✅    | ✅      | ✅       |

---

## 🚀 Próximos Passos (Sugestões)

1. ✨ Adicionar log de auditoria (quem criou qual usuário)
2. 🔔 Notificar usuário quando conta for criada
3. 📧 Enviar email com credenciais temporárias
4. 🔐 Implementar aprovação de cadastros
5. 📊 Dashboard com estatísticas de usuários por perfil
6. 🎨 Adicionar badges visuais diferentes por perfil
7. 🔍 Filtrar lista de usuários por tipo de perfil

---

## 📝 Notas Importantes

- ⚠️ Admin Django (`is_staff`) sempre tem acesso total
- ⚠️ Perfil é criado automaticamente via signal ao criar User
- ⚠️ Auto-cadastro sempre cria como "COMUM" (segurança)
- ⚠️ Interface se adapta automaticamente às permissões do usuário logado
- ⚠️ Sistema valida tanto no frontend (UX) quanto backend (segurança)

---

**Data de Implementação:** 4 de outubro de 2025  
**Status:** ✅ Implementado e Testado
