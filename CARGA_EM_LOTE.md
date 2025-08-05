# Funcionalidade de Carga em Lote

## Visao Geral

A funcionalidade de carga em lote permite importar grandes volumes de dados de uma vez, evitando a necessidade de inserir registro por registro. O sistema inclui:

- **Geracao de modelo CSV**: Template automatico com as colunas da tabela
- **Validacao de dados**: Verificacao de tipos e formatos
- **Controle de duplicidade**: Prevencao de registros duplicados
- **Modo preview**: Teste antes de importar
- **Relatorio detalhado**: Estatisticas da importacao

## Como Usar

### Passo 1: Acessar a Funcionalidade

1. Faça login no sistema
2. Vá para "Gerenciar Tabelas"
3. Selecione a tabela desejada
4. Escolha "Carga em lote" no menu

### Passo 2: Baixar o Modelo CSV

1. Clique em "Baixar modelo CSV"
2. O arquivo sera baixado com:
   - Cabecalhos das colunas
   - Exemplo de dados para cada tipo
   - Formato correto para importacao

### Passo 3: Preencher o Arquivo CSV

Use o modelo baixado como base:

```csv
Nome,Idade,Email,Ativo
João Silva,25,joao@email.com,True
Maria Santos,30,maria@email.com,False
```

**Tipos de dados suportados:**

| Tipo | Exemplo | Descricao |
|------|---------|-----------|
| Texto | "João Silva" | Texto livre |
| Número Inteiro | 25 | Números inteiros |
| Número Decimal | 123.45 | Números com decimais |
| Data | 2024-01-01 | Data no formato YYYY-MM-DD |
| Booleano | True/False | Valores verdadeiro/falso |

### Passo 4: Fazer Upload e Validar

1. Clique em "Selecione o arquivo CSV para upload"
2. Escolha o arquivo preenchido
3. O sistema validara automaticamente:
   - Presenca de todas as colunas obrigatorias
   - Tipos de dados corretos
   - Formato adequado

### Passo 5: Configurar Importacao

**Opcoes disponiveis:**

- **Pular registros duplicados**: Ignora registros identicos aos existentes
- **Modo preview**: Testa a importacao sem salvar os dados

### Passo 6: Executar Importacao

1. Clique em "Importar dados"
2. Aguarde o processamento
3. Veja o relatorio de resultados

## Relatorio de Importacao

Apos a importacao, voce vera:

- **Registros importados**: Quantidade de novos registros adicionados
- **Duplicados ignorados**: Registros que ja existiam
- **Total processados**: Total de linhas no arquivo CSV
- **Erros**: Problemas encontrados durante a importacao

## Controle de Duplicidade

O sistema previne duplicatas de varias formas:

### 1. Verificacao Completa
- Compara todos os campos (exceto ID)
- Registros identicos sao automaticamente ignorados

### 2. Tipos de Duplicidade Detectados

**Duplicatas exatas**: Todos os campos identicos
```
Nome: João Silva, Idade: 25, Email: joao@email.com
Nome: João Silva, Idade: 25, Email: joao@email.com  ← Ignorado
```

**Duplicatas parciais**: Alguns campos identicos (nao sao consideradas duplicatas)
```
Nome: João Silva, Idade: 25, Email: joao@email.com
Nome: João Silva, Idade: 30, Email: joao@email.com  ← Importado
```

### 3. Configuracao de Duplicidade

- **Ativada por padrao**: Registros duplicados sao ignorados
- **Pode ser desativada**: Para forcar importacao de todos os registros

## Validacao de Dados

### Validacoes Automaticas

1. **Colunas obrigatorias**: Todas as colunas da tabela devem estar presentes
2. **Tipos de dados**: Valores devem corresponder ao tipo definido
3. **Formatos**: Datas, numeros e booleanos sao validados

### Exemplos de Validacao

**Texto:**
```
Nome: João Silva  ← Válido
Nome: 123         ← Válido (convertido para texto)
```

**Número Inteiro:**
```
Idade: 25         ← Válido
Idade: 25.5       ← Erro (deve ser inteiro)
Idade: abc        ← Erro (deve ser número)
```

**Data:**
```
Data: 2024-01-01  ← Válido
Data: 01/01/2024  ← Erro (formato incorreto)
```

**Booleano:**
```
Ativo: True       ← Válido
Ativo: 1          ← Válido (convertido para True)
Ativo: sim        ← Válido (convertido para True)
Ativo: False      ← Válido
Ativo: 0          ← Válido (convertido para False)
```

## Tratamento de Erros

### Erros Comuns

1. **Arquivo nao encontrado**
   - Verifique se o arquivo foi selecionado corretamente

2. **Colunas faltando**
   - Use o modelo CSV fornecido
   - Verifique se todas as colunas estao presentes

3. **Tipos de dados incorretos**
   - Verifique o formato dos dados
   - Use os exemplos do modelo como referencia

4. **Arquivo corrompido**
   - Tente abrir o arquivo em um editor de texto
   - Verifique se nao ha caracteres especiais

### Solucoes

1. **Revalidar dados**: Corrija os erros e faça upload novamente
2. **Usar modo preview**: Teste antes de importar
3. **Verificar modelo**: Compare com o template fornecido

## Dicas de Uso

### Preparacao dos Dados

1. **Use o modelo fornecido**: Garante formato correto
2. **Verifique os dados**: Revise antes do upload
3. **Teste com poucos registros**: Use modo preview primeiro
4. **Backup**: Faça backup antes de importar grandes volumes

### Otimizacao

1. **Arquivos grandes**: Divida em partes menores
2. **Dados limpos**: Remova duplicatas antes do upload
3. **Formatos padronizados**: Use formatos consistentes

### Seguranca

1. **Modo preview**: Sempre teste antes de importar
2. **Backup**: Mantenha backup dos dados existentes
3. **Validacao**: Verifique os resultados apos importacao

## Exemplos Praticos

### Exemplo 1: Cadastro de Funcionarios

**Modelo gerado:**
```csv
Nome,Idade,Email,Departamento,Salario,Ativo
Exemplo de texto,123,exemplo@email.com,Exemplo de texto,123.45,True
```

**Dados para importar:**
```csv
Nome,Idade,Email,Departamento,Salario,Ativo
João Silva,25,joao@empresa.com,RH,2500.00,True
Maria Santos,30,maria@empresa.com,TI,3500.00,True
Pedro Costa,28,pedro@empresa.com,Vendas,2800.00,False
```

### Exemplo 2: Produtos

**Modelo gerado:**
```csv
Nome,Preco,Categoria,Estoque,Disponivel
Exemplo de texto,123.45,Exemplo de texto,123,True
```

**Dados para importar:**
```csv
Nome,Preco,Categoria,Estoque,Disponivel
Notebook Dell,3500.00,Eletronicos,10,True
Mouse Logitech,89.90,Perifericos,50,True
Teclado Mecanico,299.90,Perifericos,15,True
```

## Suporte

Em caso de problemas:

1. **Verifique os logs**: Use a opcao "Ver logs" no menu
2. **Teste com dados simples**: Use o modo preview
3. **Compare com o modelo**: Verifique se o formato esta correto
4. **Contate o administrador**: Para problemas tecnicos 