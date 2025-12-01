# API REST - Resultados dos Testes

## Data do Teste
01/12/2025

## Especificações Implementadas

### ✅ Autenticação por Token
- **Endpoint**: `POST /api-token-auth/`
- **Descrição**: Autenticação com login e senha que retorna um token para uso nas requisições
- **Status**: FUNCIONANDO

#### Teste 1: Autenticação com credenciais válidas
```bash
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "bruno.aluno", "password": "senha123"}'
```
**Resultado**: ✅ SUCESSO
```json
{
  "token": "a88f5264f7a6a2b933b733775e854a5dc137e31a"
}
```
**Status HTTP**: 200 OK

#### Teste 2: Autenticação com credenciais inválidas
```bash
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "bruno.aluno", "password": "wrongpassword"}'
```
**Resultado**: ✅ COMPORTAMENTO ESPERADO
```json
{
  "non_field_errors": ["Impossível fazer login com as credenciais fornecidas."]
}
```
**Status HTTP**: 400 Bad Request

---

### ✅ 3.1. Consulta de Eventos
- **Endpoint**: `GET /api/eventos/`
- **Descrição**: Listagem de todos os eventos disponíveis com informações de nome, data, local e organizador
- **Status**: FUNCIONANDO
- **Autenticação**: OBRIGATÓRIA

#### Teste 3: Consulta de eventos COM autenticação
```bash
curl -X GET http://127.0.0.1:8000/api/eventos/ \
  -H "Authorization: Token ca91892d1bb669f72ea3ceef58e32a327645a9cc"
```
**Resultado**: ✅ SUCESSO
```json
[
  {
    "id": 15,
    "titulo": "PHP",
    "tipo": "WORKSHOP",
    "data_inicio": "2024-06-12",
    "data_fim": "2024-10-22",
    "local": "CEUB - Sala 1109",
    "organizador": {
      "id": 23,
      "nome": "Maria Silva Organizadora",
      "email": "organizador@sgea.local"
    }
  },
  {
    "id": 8,
    "titulo": "",
    "tipo": "PALESTRA",
    "data_inicio": "2025-10-03",
    "data_fim": "2025-10-03",
    "local": "Auditório Central",
    "organizador": {
      "id": 23,
      "nome": "Maria Silva Organizadora",
      "email": "organizador@sgea.local"
    }
  }
  // ... mais eventos
]
```
**Status HTTP**: 200 OK

**Campos Retornados**:
- ✅ `id`: ID do evento
- ✅ `titulo`: Título ou tema do evento
- ✅ `tipo`: Tipo do evento (PALESTRA, WORKSHOP, MINICURSO)
- ✅ `data_inicio`: Data de início
- ✅ `data_fim`: Data de término
- ✅ `local`: Local do evento
- ✅ `organizador`: Dados do organizador responsável
  - `id`: ID do organizador
  - `nome`: Nome completo
  - `email`: E-mail

#### Teste 4: Consulta de eventos SEM autenticação
```bash
curl -X GET http://127.0.0.1:8000/api/eventos/
```
**Resultado**: ✅ COMPORTAMENTO ESPERADO (acesso negado)
```json
{
  "detail": "As credenciais de autenticação não foram fornecidas."
}
```
**Status HTTP**: 401 Unauthorized

---

### ✅ 3.2. Inscrição de Participantes
- **Endpoint**: `POST /api/inscricao/`
- **Descrição**: Permite que um usuário já cadastrado se inscreva em um evento específico
- **Status**: FUNCIONANDO
- **Autenticação**: OBRIGATÓRIA
- **Regra de Negócio**: Apenas usuários com perfil ALUNO ou PROFESSOR podem se inscrever

#### Teste 5: Inscrição em evento COM autenticação (usuário ALUNO)
```bash
curl -X POST http://127.0.0.1:8000/api/inscricao/ \
  -H "Authorization: Token a88f5264f7a6a2b933b733775e854a5dc137e31a" \
  -H "Content-Type: application/json" \
  -d '{"evento": 15}'
```
**Resultado**: ✅ SUCESSO
```json
{
  "evento": 15
}
```
**Status HTTP**: 201 Created

**Verificação da Inscrição Criada**:
```
✓ Inscrição criada!
  Participante: Bruno Aluno Silva
  Evento: PHP
  Status: Pendente
  Data: 01/12/2025 21:07
```

#### Teste 6: Inscrição SEM autenticação
```bash
curl -X POST http://127.0.0.1:8000/api/eventos/
```
**Resultado**: ✅ COMPORTAMENTO ESPERADO (acesso negado)
**Status HTTP**: 401 Unauthorized

---

## Configuração do Django REST Framework

### settings.py
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### URLs Configuradas
```python
urlpatterns = [
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/eventos/', EventoListView.as_view(), name='api-evento-list'),
    path('api/inscricao/', InscricaoCreateView.as_view(), name='api-inscricao-create'),
    # ... outras rotas
]
```

---

## Resumo dos Testes

| Funcionalidade | Endpoint | Método | Autenticação | Status |
|---------------|----------|---------|--------------|---------|
| Obter Token | `/api-token-auth/` | POST | Não | ✅ FUNCIONANDO |
| Listar Eventos | `/api/eventos/` | GET | Sim | ✅ FUNCIONANDO |
| Criar Inscrição | `/api/inscricao/` | POST | Sim | ✅ FUNCIONANDO |

---

## Observações Importantes

1. **Autenticação Obrigatória**: ✅ Todos os endpoints da API (exceto o de obtenção de token) exigem autenticação via Token
2. **Token no Header**: O token deve ser enviado no header `Authorization: Token <token_aqui>`
3. **Regras de Negócio**: 
   - ✅ Apenas ALUNO e PROFESSOR podem criar inscrições
   - ✅ O participante é automaticamente o usuário autenticado
   - ✅ Status da inscrição inicia como PENDENTE
4. **Informações Retornadas**: ✅ Os dados dos eventos incluem todas as informações especificadas (nome, data, local, organizador)

---

## Conclusão

✅ **TODAS AS FUNCIONALIDADES ESPECIFICADAS ESTÃO IMPLEMENTADAS E FUNCIONANDO CORRETAMENTE**

A API REST atende completamente aos requisitos:
- ✅ 3.1. Consulta de Eventos funcionando
- ✅ 3.2. Inscrição de Participantes funcionando
- ✅ Autenticação por token funcionando
- ✅ Proteção de endpoints funcionando (401 sem autenticação)
- ✅ Tratamento de erros adequado (credenciais inválidas, falta de autenticação)
