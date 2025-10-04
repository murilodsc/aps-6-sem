# 🌾 Sistema de Controle de Permissões para Propriedades Rurais

## 📋 Resumo da Implementação

Sistema de permissões baseado em perfis que controla quem pode criar e visualizar propriedades rurais com diferentes níveis de impacto ambiental.

---

## 👥 Hierarquia de Permissões por Perfil

### 1. **👤 Usuário Comum**
- **Visualização:**
  - ✅ Pode visualizar apenas propriedades de **Nível 1** (Baixo Impacto)
  - ❌ Não pode visualizar Níveis 2 e 3
- **Criação:**
  - ❌ Não pode cadastrar propriedades
- **Resumo:** Acesso somente leitura limitado ao nível mais baixo

### 2. **👔 Diretor de Divisões**
- **Visualização:**
  - ✅ Pode visualizar propriedades de **Nível 1** (Baixo Impacto)
  - ✅ Pode visualizar propriedades de **Nível 2** (Médio Impacto)
  - ❌ Não pode visualizar Nível 3
- **Criação:**
  - ✅ Pode cadastrar propriedades de **Nível 1**
  - ✅ Pode cadastrar propriedades de **Nível 2**
  - ❌ Não pode cadastrar Nível 3
- **Resumo:** Controle total sobre níveis 1 e 2

### 3. **🎖️ Ministro do Meio Ambiente**
- **Visualização:**
  - ✅ Pode visualizar propriedades de **Nível 1** (Baixo Impacto)
  - ✅ Pode visualizar propriedades de **Nível 2** (Médio Impacto)
  - ✅ Pode visualizar propriedades de **Nível 3** (Alto Impacto)
- **Criação:**
  - ✅ Pode cadastrar propriedades de **Nível 1**
  - ✅ Pode cadastrar propriedades de **Nível 2**
  - ✅ Pode cadastrar propriedades de **Nível 3**
- **Resumo:** Acesso total a todos os níveis

### 4. **⚙️ Admin/Superuser (Django)**
- **Acesso total:** Igual ao Ministro
- **Especial:** Acesso via Django Admin também

---

## 📊 Níveis de Impacto Ambiental

### **Nível 1 - Baixo Impacto** 🟢
- Contaminação localizada
- Impacto ambiental reversível
- Monitoramento básico necessário

### **Nível 2 - Médio Impacto** 🟡
- Contaminação regional
- Risco moderado aos recursos hídricos
- Necessita intervenção e acompanhamento

### **Nível 3 - Alto Impacto** 🔴
- Contaminação severa e disseminada
- Alto risco ambiental e à saúde pública
- Requer ação imediata e fiscalização rigorosa

---

## 🛠️ Implementação Técnica

### **Funções Auxiliares** (`views.py`)

#### 1. `obter_niveis_visualizacao(usuario)`
Retorna lista de níveis que o usuário pode visualizar.

```python
def obter_niveis_visualizacao(usuario):
    """
    Retorna lista de níveis de impacto que o usuário pode visualizar.
    """
    if not usuario.is_authenticated:
        return []
    
    # Admin/Superuser podem ver todos
    if usuario.is_staff or usuario.is_superuser:
        return [1, 2, 3]
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return [1]  # Padrão: apenas nível 1
    
    # Ministro pode ver todos os níveis
    if usuario.perfil.tipo_perfil == 'MINISTRO':
        return [1, 2, 3]
    
    # Diretor pode ver níveis 1 e 2
    if usuario.perfil.tipo_perfil == 'DIRETOR':
        return [1, 2]
    
    # Usuário comum pode ver apenas nível 1
    return [1]
```

**Retorna:**
- Lista de inteiros: `[1]`, `[1, 2]` ou `[1, 2, 3]`

---

#### 2. `obter_niveis_criacao(usuario)`
Retorna lista de níveis que o usuário pode criar.

```python
def obter_niveis_criacao(usuario):
    """
    Retorna lista de níveis de impacto que o usuário pode criar.
    Retorna tuplas (valor, label) para usar em select.
    """
    # Admin/Superuser podem criar todos
    if usuario.is_staff or usuario.is_superuser:
        return [
            (1, 'Nível 1 - Baixo Impacto'),
            (2, 'Nível 2 - Médio Impacto'),
            (3, 'Nível 3 - Alto Impacto'),
        ]
    
    # Ministro pode criar todos os níveis
    if usuario.perfil.tipo_perfil == 'MINISTRO':
        return [
            (1, 'Nível 1 - Baixo Impacto'),
            (2, 'Nível 2 - Médio Impacto'),
            (3, 'Nível 3 - Alto Impacto'),
        ]
    
    # Diretor pode criar níveis 1 e 2
    if usuario.perfil.tipo_perfil == 'DIRETOR':
        return [
            (1, 'Nível 1 - Baixo Impacto'),
            (2, 'Nível 2 - Médio Impacto'),
        ]
    
    # Usuário comum não pode criar propriedades
    return []
```

**Retorna:**
- Lista de tuplas `(valor, label)` ou lista vazia

---

#### 3. `pode_criar_propriedades(usuario)`
Verifica se usuário tem permissão para criar propriedades.

```python
def pode_criar_propriedades(usuario):
    """Verifica se o usuário tem permissão para criar propriedades"""
    if not usuario.is_authenticated:
        return False
    
    # Admin pode criar
    if usuario.is_staff or usuario.is_superuser:
        return True
    
    # Verifica se tem perfil
    if not hasattr(usuario, 'perfil'):
        return False
    
    # Ministro e Diretor podem criar propriedades
    # Usuário comum NÃO pode criar
    return usuario.perfil.tipo_perfil in ['MINISTRO', 'DIRETOR']
```

**Retorna:**
- `True`: Se pode criar propriedades
- `False`: Se não pode criar

---

### **View `propriedades_list`**

Lista propriedades com filtro por permissão:

```python
def propriedades_list(request):
    """Lista todas as propriedades rurais"""
    # ... código de busca e filtros ...
    
    # Filtrar por níveis que o usuário pode visualizar
    niveis_permitidos = obter_niveis_visualizacao(request.user)
    propriedades = propriedades.filter(nivel_impacto__in=niveis_permitidos)
    
    context = {
        'page_obj': page_obj,
        'nivel_filtro': nivel_filtro,
        'search': search,
        'pode_criar': pode_criar_propriedades(request.user),
        'niveis_permitidos': niveis_permitidos,
    }
    return render(request, 'core/propriedades_list.html', context)
```

**Características:**
- ✅ Filtra automaticamente propriedades por nível permitido
- ✅ Passa flag `pode_criar` para controlar botão
- ✅ Passa `niveis_permitidos` para filtros

---

### **View `propriedade_detail`**

Visualiza detalhes com validação de permissão:

```python
@login_required
def propriedade_detail(request, pk):
    """Visualiza detalhes de uma propriedade"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    
    # Verificar se usuário tem permissão para ver este nível
    niveis_permitidos = obter_niveis_visualizacao(request.user)
    if propriedade.nivel_impacto not in niveis_permitidos:
        messages.error(request, 'Você não tem permissão para visualizar propriedades deste nível!')
        return redirect('propriedades_list')
    
    return render(request, 'core/propriedade_detail.html', {'propriedade': propriedade})
```

**Proteção:**
- ❌ Bloqueia acesso direto via URL se não tiver permissão
- ✅ Redireciona com mensagem de erro

---

### **View `propriedade_create`**

Cria propriedade com validação dupla:

```python
@login_required
def propriedade_create(request):
    """Cria uma nova propriedade"""
    # Verificar se usuário pode criar propriedades
    if not pode_criar_propriedades(request.user):
        messages.error(request, 'Você não tem permissão para cadastrar propriedades!')
        return redirect('propriedades_list')
    
    niveis_permitidos = obter_niveis_criacao(request.user)
    
    if request.method == 'POST':
        try:
            nivel_escolhido = int(request.POST.get('nivel_impacto'))
            
            # Validar se o nível escolhido é permitido
            niveis_valores = [n[0] for n in niveis_permitidos]
            if nivel_escolhido not in niveis_valores:
                messages.error(request, 'Você não tem permissão para cadastrar propriedades neste nível!')
                return render(request, 'core/propriedade_form.html', {
                    'niveis_permitidos': niveis_permitidos
                })
            
            # ... resto do código de criação ...
```

**Validações:**
1. ✅ Verifica se pode criar propriedades (Usuário Comum = ❌)
2. ✅ Valida nível escolhido no POST
3. ✅ Mostra apenas níveis permitidos no select

---

### **View `propriedade_update`**

Atualiza propriedade com validação de nível:

```python
@login_required
def propriedade_update(request, pk):
    """Atualiza uma propriedade existente"""
    propriedade = get_object_or_404(PropriedadeRural, pk=pk, ativo=True)
    
    # Verificar se usuário pode ver/editar este nível
    niveis_permitidos = obter_niveis_criacao(request.user)
    niveis_valores = [n[0] for n in niveis_permitidos]
    
    if propriedade.nivel_impacto not in niveis_valores:
        messages.error(request, 'Você não tem permissão para editar propriedades deste nível!')
        return redirect('propriedades_list')
    
    # ... validação do novo nível no POST ...
```

**Proteções:**
- ❌ Bloqueia edição de propriedades de nível superior
- ✅ Valida mudança de nível

---

## 🎨 Templates Atualizados

### **`propriedades_list.html`**

#### Botão "Nova Propriedade" Condicional:
```django
<div class="page-header">
    <h1>🌾 Propriedades Rurais com Agrotóxicos Proibidos</h1>
    {% if pode_criar %}
    <a href="{% url 'propriedade_create' %}" class="btn-primary">
        + Nova Propriedade
    </a>
    {% endif %}
</div>
```

#### Filtro de Níveis Dinâmico:
```django
<select name="nivel" class="filter-select">
    <option value="">Todos os Níveis</option>
    {% if 1 in niveis_permitidos %}
    <option value="1">Nível 1 - Baixo Impacto</option>
    {% endif %}
    {% if 2 in niveis_permitidos %}
    <option value="2">Nível 2 - Médio Impacto</option>
    {% endif %}
    {% if 3 in niveis_permitidos %}
    <option value="3">Nível 3 - Alto Impacto</option>
    {% endif %}
</select>
```

---

### **`propriedade_form.html`**

#### Select de Nível Dinâmico:
```django
<select id="nivel_impacto" name="nivel_impacto" required>
    <option value="">Selecione</option>
    {% for nivel_valor, nivel_label in niveis_permitidos %}
    <option value="{{ nivel_valor }}" {% if propriedade.nivel_impacto == nivel_valor %}selected{% endif %}>
        {{ nivel_label }}
    </option>
    {% endfor %}
</select>

{% if niveis_permitidos|length == 0 %}
<small class="text-danger">Você não tem permissão para cadastrar propriedades.</small>
{% elif niveis_permitidos|length < 3 %}
<small class="text-muted">Você só pode cadastrar propriedades nos níveis permitidos para o seu perfil.</small>
{% endif %}
```

**Características:**
- ✅ Mostra apenas níveis permitidos
- ✅ Mensagem informativa sobre restrições

---

## 🔄 Fluxos de Uso

### **Fluxo 1: Usuário Comum visualiza propriedades**
1. Acessa lista de propriedades
2. Vê apenas propriedades de Nível 1
3. ❌ Não vê botão "Nova Propriedade"
4. Se tentar acessar Nível 2/3 via URL: bloqueado com erro

### **Fluxo 2: Diretor cria propriedade Nível 2**
1. Acessa "Nova Propriedade"
2. Formulário mostra apenas Níveis 1 e 2
3. Seleciona Nível 2
4. Sistema valida e salva
5. Propriedade criada com sucesso

### **Fluxo 3: Diretor tenta criar Nível 3**
1. Acessa formulário
2. ❌ Nível 3 não aparece no select
3. Se tentar forçar via POST: bloqueado com erro
4. Sistema exibe mensagem de permissão negada

### **Fluxo 4: Ministro gerencia todas**
1. Vê todas as propriedades (1, 2 e 3)
2. Pode criar qualquer nível
3. Pode editar qualquer nível
4. Acesso total ao sistema

---

## 📊 Matriz de Permissões

### **Visualização**

| Perfil / Nível | Nível 1 | Nível 2 | Nível 3 |
|----------------|---------|---------|---------|
| **Usuário Comum** | ✅ | ❌ | ❌ |
| **Diretor** | ✅ | ✅ | ❌ |
| **Ministro** | ✅ | ✅ | ✅ |
| **Admin** | ✅ | ✅ | ✅ |

### **Criação/Edição**

| Perfil / Nível | Nível 1 | Nível 2 | Nível 3 |
|----------------|---------|---------|---------|
| **Usuário Comum** | ❌ | ❌ | ❌ |
| **Diretor** | ✅ | ✅ | ❌ |
| **Ministro** | ✅ | ✅ | ✅ |
| **Admin** | ✅ | ✅ | ✅ |

---

## 🔒 Segurança

### **Camadas de Proteção:**

1. **Filtro no QuerySet:**
   ```python
   propriedades = propriedades.filter(nivel_impacto__in=niveis_permitidos)
   ```
   - ✅ Usuário nunca vê dados não autorizados

2. **Validação no Detail:**
   ```python
   if propriedade.nivel_impacto not in niveis_permitidos:
       return redirect('propriedades_list')
   ```
   - ✅ Bloqueia acesso direto via URL

3. **Validação no Create/Update:**
   ```python
   if nivel_escolhido not in niveis_valores:
       messages.error(request, 'Permissão negada!')
   ```
   - ✅ Previne manipulação de formulário

4. **Interface Adaptável:**
   - ✅ Select só mostra opções permitidas
   - ✅ Botões aparecem conforme permissão

---

## ✅ Casos de Teste

### **Teste 1: Usuário Comum acessa lista**
- ✅ Vê apenas propriedades Nível 1
- ✅ Não vê botão "Nova Propriedade"
- ✅ Filtro mostra apenas Nível 1

### **Teste 2: Usuário Comum tenta acessar Nível 3 via URL**
- ✅ Bloqueado com mensagem de erro
- ✅ Redirecionado para lista

### **Teste 3: Diretor cria Nível 2**
- ✅ Formulário mostra Níveis 1 e 2
- ✅ Pode selecionar e salvar Nível 2
- ✅ Propriedade criada com sucesso

### **Teste 4: Diretor tenta criar Nível 3 via POST manipulado**
- ✅ Backend valida e rejeita
- ✅ Mensagem de erro exibida
- ✅ Propriedade não é criada

### **Teste 5: Ministro acessa tudo**
- ✅ Vê todas as propriedades (1, 2, 3)
- ✅ Pode criar qualquer nível
- ✅ Pode editar qualquer nível

---

## 🎯 Benefícios da Implementação

1. **🔐 Segurança em Camadas:**
   - Backend valida tudo
   - Frontend adapta interface
   - Impossível burlar permissões

2. **👁️ Privacidade de Dados:**
   - Usuários comuns não veem casos graves (Nível 3)
   - Informações sensíveis protegidas

3. **📊 Hierarquia Clara:**
   - Cada perfil tem escopo bem definido
   - Escalação gradual de responsabilidade

4. **🎨 UX Intuitiva:**
   - Usuário só vê opções válidas
   - Sem tentativas frustradas

5. **⚡ Performance:**
   - Filtro no banco de dados
   - Não carrega dados desnecessários

---

## 🚀 Melhorias Futuras (Sugestões)

1. ✨ Log de auditoria (quem visualizou Nível 3)
2. 🔔 Notificações para Ministros sobre novos Nível 3
3. 📧 Relatórios periódicos por nível
4. 🗺️ Mapa interativo com níveis por cor
5. 📈 Dashboard com estatísticas por nível
6. 🔍 Busca avançada por critérios de impacto
7. 📱 App mobile com mesmas permissões

---

## 📝 Notas Técnicas

- ⚠️ Propriedades nunca são deletadas, apenas desativadas (`ativo=False`)
- ⚠️ `usuario_cadastro` registra quem criou a propriedade
- ⚠️ Filtro `nivel_impacto__in` garante performance
- ⚠️ Validação dupla: frontend (UX) + backend (segurança)
- ⚠️ Permissões verificadas em tempo real, não cached

---

**Data de Implementação:** 4 de outubro de 2025  
**Status:** ✅ Implementado e Testado  
**Integração:** Sistema de permissões de usuários + propriedades
