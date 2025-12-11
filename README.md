# Automação Educacional e Gestão de Sistemas (AEGS) © 2027.

Projeto Django para cadastro de usuários, gerenciamento de eventos acadêmicos, inscrições e emissão de certificados.

##### [Documentação Formal](docs/docs-prog-web.pdf)

## Alunos
- Ângelo: 22409042
- Augusto: 22400555
- Luana: 22404503

## Requisitos

- Python 3.13 (ou superior compatível)
- Virtualenv ativado (`python -m venv .venv && source .venv/bin/activate`)
- Banco de dados SQLite (arquivo `db.sqlite3` incluído)

## Configuração

1. Instale as dependências principais:

	```bash
	pip install -r requirements.txt
	```

	> Caso o arquivo `requirements.txt` não exista, instale manualmente: `pip install django fpdf2`.

2. Execute as migrações do banco:

	```bash
	python manage.py migrate
	```

3. Crie um usuário administrador:

	```bash
	python manage.py createsuperuser
	```

4. Rode os testes para validar as regras de negócio:

	```bash
	python manage.py test
	```

5. Carregue os dados de exemplo, população inicial dos dados:

	```bash
	python database/load_sample_data.py
	```

	**Credenciais de Acesso (Ambiente de Teste):**

	| Perfil | Usuário | Senha |
	|--------|---------|-------|
	| **Admin** | `admin` | `Admin@123` |
	| **Organizador** | `organizador` | `Admin@123` |
	| **Aluno** | `aluno` | `Aluno@123` |
	| **Professor** | `professor` | `Professor@123` |

	> Outros usuários de exemplo também são criados com o padrão `Perfil@123`.

6. **Configuração de E-mail (Opcional):**

	O sistema envia e-mails automáticos para confirmação de inscrições e notificações de certificados. Por padrão, os e-mails são impressos no console do servidor (modo desenvolvimento).

	Para configurar envio real de e-mails via SMTP (ex.: Gmail), edite `gestor_eventos/settings.py` e descomente as linhas do backend SMTP, ajustando as credenciais:

	```python
	EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
	EMAIL_HOST = 'smtp.gmail.com'
	EMAIL_PORT = 587
	EMAIL_USE_TLS = True
	EMAIL_HOST_USER = 'seu-email@gmail.com'
	EMAIL_HOST_PASSWORD = 'sua-senha-de-app'  # Use senha de app para Gmail
	```

	> **Nota:** Para Gmail, ative a autenticação de dois fatores e gere uma senha de app. Para desenvolvimento, mantenha o backend console para evitar problemas de conectividade.

7. Suba o servidor de desenvolvimento:

	```bash
	python manage.py runserver
	```

	Abra http://127.0.0.1:8000 para visualizar o layout estático (templates em `api/templates/api/` e estilos em `api/static/api/`).

## Automação

O sistema possui um comando para emissão automática de certificados para eventos finalizados. O comando verifica inscrições confirmadas com presença registrada e gera os certificados pendentes.

```bash
python manage.py emitir_certificados
```

## Estrutura dos Modelos

- `Usuario`: extensão de `AbstractUser` com campos de nome, telefone, instituição e perfil (Aluno, Professor, Organizador, Admin).
- `Evento`: cadastro de eventos com tipo, período, local, capacidade e organizador responsável.
- `Inscricao`: vincula participantes (alunos/professores) aos eventos, controlando status, presença e limite de vagas.
- `Certificado`: emissão vinculada a inscrições confirmadas e com presença registrada, incluindo carga horária e validade.

O arquivo `docs/diagrama-logico.pdf` traz uma visão resumida das entidades e relacionamentos.

## Protótipo de Interface

- `api/templates/api/base.html`: layout base com navegação e rodapé.
- `api/static/api/styles.css`: estilos minimalistas responsivos.
- Fluxos específicos disponíveis em `/prototipos/`:
	- `/` ou `/prototipos/cadastro-usuarios/` – formulário e regras para criação de contas.
	- `/prototipos/cadastro-eventos/` – tela de cadastro de eventos com checklist do organizador.
	- `/prototipos/inscricao-usuarios/` – controle de inscrições, vagas e presença.
	- `/prototipos/emissao-certificados/` – emissão manual com pré-visualização.
	- `/prototipos/autenticacao/` – tela de login e recuperação de acesso.

Os templates usam `TemplateView` configurado em `gestor_eventos/urls.py` para facilitar a navegação durante a apresentação.

## Script SQL

O script `database/schema.sql` recria o banco SQLite (mesmo schema utilizado pelo Django) com constraints e dados iniciais (usuários, eventos, inscrições e certificado de exemplo). Execute-o via CLI: `sqlite3 db.sqlite3 < database/schema.sql`.

## Diagrama MER
![Diagrama](docs/diagrama-MER-inicial.png)

## Representação Visual dos Casos de Uso
![Casos de Uso](docs/casos-uso.png)
