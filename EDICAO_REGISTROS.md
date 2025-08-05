# 📝 Edição e Exclusão de Registros

Guia completo para editar e excluir registros no Sistema de Cadastro.

## 🎯 Funcionalidades Disponíveis

### ✅ **Interface Web (Streamlit)**
- **Editar registros** - Modificar dados existentes
- **Excluir registros** - Remover registros permanentemente
- **Seleção visual** - Escolher registro para editar/excluir
- **Validação automática** - Verificação de tipos de dados
- **Confirmação de exclusão** - Prevenção de exclusões acidentais

### 🔧 **API REST**
- **GET** `/api/tables/{nome}/records/{id}` - Obter registro específico
- **PUT** `/api/tables/{nome}/records/{id}` - Atualizar registro
- **DELETE** `/api/tables/{nome}/records/{id}` - Excluir registro

## 🌐 Interface Web

### **Como Editar Registros**

1. **Acessar** a página "Gerenciar tabelas existentes"
2. **Selecionar** a tabela desejada
3. **Escolher** "Editar registro" no menu
4. **Selecionar** o registro na lista dropdown
5. **Modificar** os campos desejados
6. **Clicar** em "Atualizar registro"

### **Como Excluir Registros**

1. **Acessar** a página "Gerenciar tabelas existentes"
2. **Selecionar** a tabela desejada
3. **Escolher** "Excluir registro" no menu
4. **Selecionar** o registro na lista dropdown
5. **Confirmar** a exclusão marcando a caixa
6. **Clicar** em "Excluir registro"

### **Características da Interface**

- ✅ **Seleção intuitiva** - Dropdown com informações do registro
- ✅ **Formulário dinâmico** - Campos baseados no tipo de dados
- ✅ **Validação em tempo real** - Verificação de tipos
- ✅ **Confirmação de segurança** - Para exclusões
- ✅ **Feedback visual** - Mensagens de sucesso/erro

## 🔧 API REST

### **Endpoints Disponíveis**

#### **1. Obter Registro Específico**
```bash
GET http://localhost:5000/api/tables/{nome}/records/{id}
```

**Exemplo:**
```bash
curl http://localhost:5000/api/tables/pessoas/records/1
```

**Resposta:**
```json
{
  "success": true,
  "record": {
    "id": 1,
    "nome": "João Silva",
    "email": "joao@email.com",
    "idade": 30
  }
}
```

#### **2. Atualizar Registro**
```bash
PUT http://localhost:5000/api/tables/{nome}/records/{id}
Content-Type: application/json
```

**Exemplo:**
```bash
curl -X PUT http://localhost:5000/api/tables/pessoas/records/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva Atualizado",
    "email": "joao.novo@email.com",
    "idade": 35
  }'
```

**Resposta:**
```json
{
  "success": true,
  "message": "Registro atualizado com sucesso",
  "affected_rows": 1
}
```

#### **3. Excluir Registro**
```bash
DELETE http://localhost:5000/api/tables/{nome}/records/{id}
```

**Exemplo:**
```bash
curl -X DELETE http://localhost:5000/api/tables/pessoas/records/2
```

**Resposta:**
```json
{
  "success": true,
  "message": "Registro excluído com sucesso",
  "affected_rows": 1
}
```

## 📝 Exemplos de Uso

### **Python com requests**

```python
import requests

# Configuração
BASE_URL = "http://localhost:5000/api"

def editar_registro(tabela, id_registro, dados):
    """Edita um registro via API."""
    url = f"{BASE_URL}/tables/{tabela}/records/{id_registro}"
    response = requests.put(url, json=dados)
    
    if response.status_code == 200:
        print("✅ Registro atualizado!")
        return response.json()
    else:
        print(f"❌ Erro: {response.json()}")
        return None

def excluir_registro(tabela, id_registro):
    """Exclui um registro via API."""
    url = f"{BASE_URL}/tables/{tabela}/records/{id_registro}"
    response = requests.delete(url)
    
    if response.status_code == 200:
        print("✅ Registro excluído!")
        return response.json()
    else:
        print(f"❌ Erro: {response.json()}")
        return None

def obter_registro(tabela, id_registro):
    """Obtém um registro específico."""
    url = f"{BASE_URL}/tables/{tabela}/records/{id_registro}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()['record']
    else:
        print(f"❌ Erro: {response.json()}")
        return None

# Exemplos de uso
if __name__ == "__main__":
    # Editar registro
    dados_atualizacao = {
        "nome": "Maria Silva",
        "email": "maria@email.com",
        "idade": 28
    }
    editar_registro("pessoas", 1, dados_atualizacao)
    
    # Excluir registro
    excluir_registro("pessoas", 2)
    
    # Obter registro
    registro = obter_registro("pessoas", 1)
    print(f"Registro: {registro}")
```

### **JavaScript/Fetch**

```javascript
// Configuração
const BASE_URL = "http://localhost:5000/api";

// Editar registro
async function editarRegistro(tabela, id, dados) {
    try {
        const response = await fetch(`${BASE_URL}/tables/${tabela}/records/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('✅ Registro atualizado!', result);
            return result;
        } else {
            console.error('❌ Erro:', result);
            return null;
        }
    } catch (error) {
        console.error('❌ Erro de conexão:', error);
        return null;
    }
}

// Excluir registro
async function excluirRegistro(tabela, id) {
    try {
        const response = await fetch(`${BASE_URL}/tables/${tabela}/records/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('✅ Registro excluído!', result);
            return result;
        } else {
            console.error('❌ Erro:', result);
            return null;
        }
    } catch (error) {
        console.error('❌ Erro de conexão:', error);
        return null;
    }
}

// Exemplos de uso
editarRegistro('pessoas', 1, {
    nome: 'João Atualizado',
    email: 'joao.novo@email.com',
    idade: 35
});

excluirRegistro('pessoas', 2);
```

## 🛡️ Segurança e Validação

### **Validações Implementadas**

- ✅ **Verificação de existência** - Registro deve existir
- ✅ **Validação de tipos** - Dados devem ser do tipo correto
- ✅ **Sanitização SQL** - Prevenção de SQL injection
- ✅ **Confirmação de exclusão** - Interface web
- ✅ **Logs de operação** - Rastreamento de mudanças

### **Boas Práticas**

1. **Sempre verificar** se o registro existe antes de editar/excluir
2. **Validar dados** antes de enviar para a API
3. **Usar HTTPS** em produção
4. **Implementar autenticação** para operações sensíveis
5. **Fazer backup** antes de operações em massa

## 🔄 Fluxo de Trabalho

### **Para Edição de Registros**

1. **Identificar** o registro a ser editado
2. **Obter** dados atuais via API ou interface
3. **Modificar** apenas os campos necessários
4. **Validar** os novos dados
5. **Enviar** atualização via API
6. **Verificar** se a operação foi bem-sucedida

### **Para Exclusão de Registros**

1. **Identificar** o registro a ser excluído
2. **Verificar** dependências (se houver)
3. **Confirmar** a exclusão
4. **Executar** a exclusão
5. **Verificar** se foi removido corretamente

## 🚨 Tratamento de Erros

### **Códigos de Erro Comuns**

- **400** - Dados inválidos fornecidos
- **404** - Registro não encontrado
- **500** - Erro interno do servidor

### **Exemplo de Tratamento**

```python
try:
    response = requests.put(url, json=dados)
    
    if response.status_code == 200:
        print("✅ Sucesso!")
    elif response.status_code == 404:
        print("❌ Registro não encontrado")
    elif response.status_code == 400:
        print("❌ Dados inválidos")
    else:
        print(f"❌ Erro {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Erro de conexão: {e}")
```

## 📊 Monitoramento

### **Logs Recomendados**

- ✅ **Operações de edição** - Quem editou o quê
- ✅ **Operações de exclusão** - Quem excluiu o quê
- ✅ **Tentativas de acesso** - Logs de segurança
- ✅ **Performance** - Tempo de resposta das operações

### **Métricas Úteis**

- 📈 **Taxa de edição** - Quantos registros são editados
- 📉 **Taxa de exclusão** - Quantos registros são excluídos
- ⏱️ **Tempo médio** de operações
- 🚨 **Erros frequentes** - Para correção

---

**🎯 Sistema completo de CRUD implementado com sucesso!** 