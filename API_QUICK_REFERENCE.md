# Guia Rápido da API REST - SGEA

## Base URL
```
http://127.0.0.1:8000
```

## Autenticação

### 1. Obter Token de Autenticação
**Endpoint**: `POST /api-token-auth/`

**Request**:
```bash
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seu_usuario",
    "password": "sua_senha"
  }'
```

**Response (Sucesso)**:
```json
{
  "token": "ca91892d1bb669f72ea3ceef58e32a327645a9cc"
}
```

**Response (Erro)**:
```json
{
  "non_field_errors": ["Impossível fazer login com as credenciais fornecidas."]
}
```

---

## Endpoints Disponíveis

### 2. Listar Todos os Eventos
**Endpoint**: `GET /api/eventos/`  
**Autenticação**: Obrigatória

**Request**:
```bash
curl -X GET http://127.0.0.1:8000/api/eventos/ \
  -H "Authorization: Token SEU_TOKEN_AQUI"
```

**Response**:
```json
[
  {
    "id": 15,
    "titulo": "Workshop de PHP",
    "tipo": "WORKSHOP",
    "data_inicio": "2024-06-12",
    "data_fim": "2024-10-22",
    "local": "CEUB - Sala 1109",
    "organizador": {
      "id": 23,
      "nome": "Maria Silva Organizadora",
      "email": "organizador@sgea.local"
    }
  }
]
```

### 3. Inscrever-se em um Evento
**Endpoint**: `POST /api/inscricao/`  
**Autenticação**: Obrigatória  
**Perfis Permitidos**: ALUNO, PROFESSOR

**Request**:
```bash
curl -X POST http://127.0.0.1:8000/api/inscricao/ \
  -H "Authorization: Token SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "evento": 15
  }'
```

**Response (Sucesso)**:
```json
{
  "evento": 15
}
```

**Status HTTP**: 201 Created

---

## Exemplos de Uso Completo

### Fluxo: Autenticar → Listar Eventos → Inscrever-se

```bash
# 1. Obter token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "bruno.aluno", "password": "senha123"}' \
  | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

echo "Token obtido: $TOKEN"

# 2. Listar eventos disponíveis
curl -X GET http://127.0.0.1:8000/api/eventos/ \
  -H "Authorization: Token $TOKEN"

# 3. Inscrever-se no evento ID 15
curl -X POST http://127.0.0.1:8000/api/inscricao/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"evento": 15}'
```

---

## Códigos de Status HTTP

| Código | Significado | Quando Ocorre |
|--------|-------------|---------------|
| 200 | OK | Consulta bem-sucedida |
| 201 | Created | Inscrição criada com sucesso |
| 400 | Bad Request | Credenciais inválidas ou dados incorretos |
| 401 | Unauthorized | Token não fornecido ou inválido |
| 404 | Not Found | Evento não encontrado |

---

## Usuários de Teste Disponíveis

| Username | Password | Perfil | Pode se inscrever? |
|----------|----------|--------|-------------------|
| admin | admin123 | ADMIN | ❌ Não |
| organizador | senha123 | ORGANIZADOR | ❌ Não |
| bruno.aluno | senha123 | ALUNO | ✅ Sim |
| ana.prof | senha123 | PROFESSOR | ✅ Sim |

---

## Regras de Negócio

1. **Autenticação**: Todos os endpoints (exceto `/api-token-auth/`) exigem autenticação
2. **Token no Header**: Use o formato `Authorization: Token <seu_token>`
3. **Inscrições**: Apenas usuários ALUNO ou PROFESSOR podem se inscrever em eventos
4. **Status Inicial**: Inscrições criadas via API iniciam com status PENDENTE
5. **Participante Automático**: O participante da inscrição é sempre o usuário autenticado

---

## Testando com Python

```python
import requests

# Base URL
BASE_URL = "http://127.0.0.1:8000"

# 1. Autenticar
response = requests.post(f"{BASE_URL}/api-token-auth/", json={
    "username": "bruno.aluno",
    "password": "senha123"
})
token = response.json()["token"]

# Headers com autenticação
headers = {
    "Authorization": f"Token {token}"
}

# 2. Listar eventos
eventos = requests.get(f"{BASE_URL}/api/eventos/", headers=headers)
print(eventos.json())

# 3. Inscrever-se no primeiro evento
primeiro_evento_id = eventos.json()[0]["id"]
inscricao = requests.post(
    f"{BASE_URL}/api/inscricao/",
    headers=headers,
    json={"evento": primeiro_evento_id}
)
print(f"Inscrição criada: {inscricao.status_code}")
```

---

## Testando com JavaScript (Fetch API)

```javascript
const BASE_URL = "http://127.0.0.1:8000";

// 1. Autenticar
async function autenticar() {
  const response = await fetch(`${BASE_URL}/api-token-auth/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'bruno.aluno',
      password: 'senha123'
    })
  });
  const data = await response.json();
  return data.token;
}

// 2. Listar eventos
async function listarEventos(token) {
  const response = await fetch(`${BASE_URL}/api/eventos/`, {
    headers: { 'Authorization': `Token ${token}` }
  });
  return await response.json();
}

// 3. Inscrever-se em evento
async function inscrever(token, eventoId) {
  const response = await fetch(`${BASE_URL}/api/inscricao/`, {
    method: 'POST',
    headers: {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ evento: eventoId })
  });
  return await response.json();
}

// Uso
(async () => {
  const token = await autenticar();
  const eventos = await listarEventos(token);
  console.log('Eventos:', eventos);
  
  if (eventos.length > 0) {
    const resultado = await inscrever(token, eventos[0].id);
    console.log('Inscrição:', resultado);
  }
})();
```

---

## Troubleshooting

### Erro: "As credenciais de autenticação não foram fornecidas"
**Solução**: Certifique-se de incluir o header `Authorization: Token <seu_token>`

### Erro: "Impossível fazer login com as credenciais fornecidas"
**Solução**: Verifique se o username e password estão corretos

### Erro: "A instância de usuario com id X não existe"
**Solução**: Este erro ocorre quando um usuário ADMIN ou ORGANIZADOR tenta se inscrever. Apenas ALUNO e PROFESSOR podem criar inscrições.
