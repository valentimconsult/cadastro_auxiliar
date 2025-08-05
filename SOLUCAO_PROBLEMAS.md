# 🔧 Solução de Problemas - Sistema de Cadastro

Guia para resolver problemas comuns do sistema.

## 🖼️ Problemas com Logo

### **Problema: Logo muito grande**
**Sintomas:**
- Logo ocupa muito espaço na tela
- Interface fica desproporcional
- Performance lenta

**Soluções:**

#### **1. Otimização Automática**
```powershell
# Executar otimização automática
.\start-app.ps1 optimize
```

#### **2. Redimensionamento Manual**
```python
# Executar script de otimização
python otimizar_sistema.py
```

#### **3. Configuração Manual**
1. Acesse **Configurações do sistema**
2. Remova a logo atual
3. Faça upload de uma nova logo com tamanho máximo:
   - **Largura:** 300 pixels
   - **Altura:** 200 pixels
   - **Formato:** PNG ou JPG

### **Problema: Logo não aparece**
**Sintomas:**
- Logo não carrega
- Erro de arquivo não encontrado

**Soluções:**
1. Verificar se o arquivo existe em `data/logos/`
2. Executar otimização do sistema
3. Reupload da logo

## ⚡ Problemas de Performance

### **Problema: Sistema lento**
**Sintomas:**
- Carregamento lento
- Interface responsiva
- Alto uso de memória

**Soluções:**

#### **1. Otimização Completa**
```powershell
# Executar todas as otimizações
.\start-app.ps1 optimize
```

#### **2. Limpeza Manual**
```powershell
# Parar aplicação
.\start-app.ps1 stop

# Limpar Docker
.\start-app.ps1 clean

# Rebuild da imagem
.\start-app.ps1 build

# Reiniciar
.\start-app.ps1 start
```

#### **3. Verificação de Recursos**
```powershell
# Verificar status
.\start-app.ps1 status
```

### **Problema: Status "RUNNING..." constante**
**Explicação:** Isso é **normal** do Streamlit. O status "RUNNING..." indica que a aplicação está funcionando corretamente.

**Se estiver causando problemas:**
1. Verificar se não há loops infinitos no código
2. Executar otimização do sistema
3. Reiniciar a aplicação

## 🗄️ Problemas de Banco de Dados

### **Problema: Erro de conexão**
**Sintomas:**
- Erro ao acessar dados
- Tabelas não carregam

**Soluções:**
```powershell
# Parar aplicação
.\start-app.ps1 stop

# Verificar arquivo do banco
ls data/data.db

# Reiniciar aplicação
.\start-app.ps1 start
```

### **Problema: Erro ao editar registros**
**Sintomas:**
- "Missing Submit Button" na interface
- "invalid literal for int() with base 10: ''"
- Erro ao carregar dados para edição

**Soluções:**

#### **1. Rebuild da aplicação**
```powershell
# Rebuild completo
.\start-app.ps1 build
.\start-app.ps1 restart
```

#### **2. Testar funcionalidade**
```python
# Executar script de teste
python testar_edicao.py
```

#### **3. Verificar dados**
```powershell
# Verificar logs
.\start-app.ps1 logs

# Testar API
curl http://localhost:5000/api/health
```

#### **4. Limpeza manual**
```powershell
# Parar aplicação
.\start-app.ps1 stop

# Limpar cache
.\start-app.ps1 clean

# Rebuild e reiniciar
.\start-app.ps1 build
.\start-app.ps1 start
```

### **Problema: Dados corrompidos**
**Soluções:**
1. Fazer backup dos dados
2. Executar otimização do banco
3. Verificar integridade

## 🌐 Problemas de Rede

### **Problema: API não responde**
**Sintomas:**
- Erro 500 na API
- Endpoints não funcionam

**Soluções:**
```powershell
# Verificar logs
.\start-app.ps1 logs

# Reiniciar aplicação
.\start-app.ps1 restart

# Verificar portas
netstat -ano | findstr :5000
netstat -ano | findstr :8501
```

### **Problema: Porta já em uso**
**Soluções:**
1. Parar outros serviços na porta
2. Alterar porta no `docker-compose.yml`
3. Reiniciar aplicação

## 🔧 Scripts de Manutenção

### **Otimização Automática**
```powershell
# Executar otimização completa
.\start-app.ps1 optimize
```

**O que faz:**
- ✅ Redimensiona logos grandes
- ✅ Otimiza banco de dados
- ✅ Limpa cache
- ✅ Verifica configurações
- ✅ Cria diretórios necessários

### **Limpeza Manual**
```powershell
# Limpar recursos Docker
.\start-app.ps1 clean

# Rebuild da imagem
.\start-app.ps1 build

# Reiniciar aplicação
.\start-app.ps1 restart
```

## 📊 Monitoramento

### **Verificar Status**
```powershell
# Status dos containers
.\start-app.ps1 status

# Ver logs em tempo real
.\start-app.ps1 logs
```

### **Métricas Importantes**
- **Uso de CPU:** Deve estar abaixo de 80%
- **Uso de Memória:** Deve estar abaixo de 2GB
- **Tamanho do Banco:** Monitorar crescimento
- **Logs de Erro:** Verificar regularmente

## 🚨 Problemas Críticos

### **Sistema não inicia**
**Soluções:**
1. Verificar se Docker está rodando
2. Verificar se portas estão livres
3. Executar rebuild completo
4. Verificar logs detalhados

### **Perda de dados**
**Prevenção:**
1. Fazer backup regular do `data/data.db`
2. Usar volumes Docker para persistência
3. Monitorar integridade do banco

## 💡 Dicas de Performance

### **Para Logos**
- ✅ Use imagens com tamanho máximo 300x200 pixels
- ✅ Formato PNG ou JPG
- ✅ Otimize antes do upload
- ✅ Use compressão adequada

### **Para Banco de Dados**
- ✅ Execute otimização regular
- ✅ Monitore tamanho do banco
- ✅ Faça backup periódico
- ✅ Limpe dados antigos

### **Para Sistema**
- ✅ Reinicie periodicamente
- ✅ Monitore recursos
- ✅ Use otimização automática
- ✅ Mantenha logs organizados

## 📞 Suporte

### **Logs Importantes**
```powershell
# Logs da aplicação
docker-compose logs cadastro-app

# Logs da API
docker-compose logs api-server

# Logs completos
docker-compose logs
```

### **Informações do Sistema**
```powershell
# Status dos containers
docker-compose ps

# Uso de recursos
docker system df

# Informações detalhadas
docker stats
```

---

**🔧 Sistema otimizado e funcionando perfeitamente!** 