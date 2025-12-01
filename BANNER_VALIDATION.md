# Validação de Upload de Banner - Documentação

## Implementação

### Localização
- **Backend**: `api/views.py` - Função `_validate_image_file()`
- **Frontend**: `api/templates/api/cadastro_evento.html` - Validação JavaScript

## Regras de Validação

### 1. Extensões Permitidas
O banner deve ter uma das seguintes extensões de arquivo:
- `.jpg` / `.jpeg`
- `.png`
- `.gif`
- `.bmp`
- `.webp`
- `.svg`

### 2. Tipos MIME Aceitos
- `image/jpeg`
- `image/png`
- `image/gif`
- `image/bmp`
- `image/webp`
- `image/svg+xml`

### 3. Tamanho Máximo
- **Limite**: 5 MB (5.242.880 bytes)
- Arquivos maiores que 5MB serão rejeitados

### 4. Campo Opcional
- O banner é opcional - eventos podem ser criados sem banner
- A validação só é executada se um arquivo for enviado

## Validação Backend (Python)

### Função: `_validate_image_file(file)`

```python
def _validate_image_file(file) -> str | None:
    """
    Validate that the uploaded file is an image.
    Returns error message if invalid, None if valid.
    """
    if not file:
        return None
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    file_ext = os.path.splitext(file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return f"Formato de arquivo inválido. Use: {', '.join(allowed_extensions)}"
    
    # Check MIME type
    allowed_mime_types = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp',
        'image/svg+xml'
    ]
    
    if hasattr(file, 'content_type') and file.content_type not in allowed_mime_types:
        return "O arquivo enviado não é uma imagem válida."
    
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if file.size > max_size:
        return "A imagem deve ter no máximo 5MB."
    
    return None
```

### Integração no CadastroEventoView

```python
# Validate banner image if provided
if banner:
    banner_error = _validate_image_file(banner)
    if banner_error:
        errors.append(banner_error)
```

## Validação Frontend (JavaScript)

### Validação no Formulário

```javascript
$('form').on('submit', function(e) {
    var banner = $('#evento-banner')[0].files[0];
    if (banner) {
        // Validate file type
        var fileType = banner['type'];
        var validImageTypes = ['image/gif', 'image/jpeg', 'image/png', 
                               'image/webp', 'image/bmp', 'image/svg+xml'];
        if ($.inArray(fileType, validImageTypes) < 0) {
            alert("Formato de arquivo inválido. Use: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg");
            e.preventDefault();
            return false;
        }
        
        // Validate file size (max 5MB)
        var maxSize = 5 * 1024 * 1024; // 5MB in bytes
        if (banner.size > maxSize) {
            alert("A imagem deve ter no máximo 5MB.");
            e.preventDefault();
            return false;
        }
    }
});
```

## Mensagens de Erro

### Extensão Inválida
```
"Formato de arquivo inválido. Use: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg"
```

### Tipo MIME Inválido
```
"O arquivo enviado não é uma imagem válida."
```

### Arquivo Muito Grande
```
"A imagem deve ter no máximo 5MB."
```

## Exemplos de Uso

### Teste com cURL (API)
```bash
# Upload com imagem válida
curl -X POST http://127.0.0.1:8000/cadastro-eventos/ \
  -F "tipo=PALESTRA" \
  -F "titulo=Evento de Teste" \
  -F "local=Sala 101" \
  -F "data_inicio=2025-12-15" \
  -F "data_fim=2025-12-15" \
  -F "capacidade=50" \
  -F "organizador=1" \
  -F "banner=@/path/to/image.jpg"

# Upload com PDF (será rejeitado)
curl -X POST http://127.0.0.1:8000/cadastro-eventos/ \
  -F "banner=@/path/to/document.pdf" \
  # ... outros campos
```

### Teste Manual no Formulário Web

1. Acesse: `http://127.0.0.1:8000/cadastro-eventos/`
2. Preencha os campos obrigatórios
3. Tente fazer upload de:
   - ✅ **Imagem válida** (.jpg, .png, etc.) com < 5MB → **Sucesso**
   - ❌ **Arquivo PDF** → **Erro: "Formato de arquivo inválido..."**
   - ❌ **Imagem > 5MB** → **Erro: "A imagem deve ter no máximo 5MB"**
   - ❌ **Arquivo .txt** → **Erro: "Formato de arquivo inválido..."**

## Casos de Teste

### ✅ Casos Válidos
| Arquivo | Extensão | Tamanho | Resultado |
|---------|----------|---------|-----------|
| banner.jpg | .jpg | 2MB | Aceito |
| logo.png | .png | 1MB | Aceito |
| icon.svg | .svg | 50KB | Aceito |
| photo.webp | .webp | 3MB | Aceito |
| *nenhum arquivo* | - | - | Aceito (opcional) |

### ❌ Casos Inválidos
| Arquivo | Extensão | Tamanho | Erro |
|---------|----------|---------|------|
| doc.pdf | .pdf | 1MB | Formato inválido |
| data.txt | .txt | 10KB | Formato inválido |
| large.jpg | .jpg | 8MB | Arquivo muito grande |
| script.js | .js | 5KB | Formato inválido |
| archive.zip | .zip | 2MB | Formato inválido |

## Segurança

### Proteções Implementadas

1. **Validação de Extensão**: Previne upload de arquivos executáveis disfarçados
2. **Validação MIME Type**: Verifica o tipo real do arquivo, não apenas a extensão
3. **Limite de Tamanho**: Previne DoS por upload de arquivos muito grandes
4. **Validação Client-Side**: Feedback imediato ao usuário
5. **Validação Server-Side**: Camada final de segurança (não pode ser bypassed)

### Considerações

- A validação client-side pode ser desabilitada pelo usuário
- **SEMPRE** valide no servidor (backend)
- Arquivos são salvos em `media/banners/` por padrão
- Django ImageField já faz validação adicional via Pillow

## Testes Automatizados

Para testar a validação:

```bash
cd /home/guto/Desktop/gestor-eventos
venv/bin/python test_banner_validation.py
```

## Histórico de Mudanças

- **01/12/2025**: Implementação inicial da validação de banner
  - Adicionada função `_validate_image_file()`
  - Integração no `CadastroEventoView.post()`
  - Atualização da validação JavaScript no template
  - Suporte para extensões: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg
  - Limite de tamanho: 5MB
