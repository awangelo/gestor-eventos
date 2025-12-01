# Sistema de Login e Controle de Acesso Baseado em Perfis

## Visão Geral

O sistema agora implementa autenticação obrigatória e controle de acesso baseado em perfis de usuário. Todos os usuários devem fazer login antes de acessar qualquer funcionalidade do sistema.

## Perfis de Usuário e Permissões

### 1. ADMIN (Administrador)
**Acesso Total** - Pode acessar todas as funcionalidades do sistema:
- ✅ Cadastro de Usuários
- ✅ Cadastro de Eventos
- ✅ Gerenciar Inscrições (de qualquer usuário)
- ✅ Emitir Certificados

### 2. ORGANIZADOR
**Gestão de Eventos e Certificados**:
- ✅ Cadastro de Eventos
- ✅ Gerenciar Inscrições nos eventos
- ✅ Emitir Certificados para participantes
- ❌ Cadastro de Usuários (apenas Admin)

### 3. ALUNO / PROFESSOR
**Participação em Eventos**:
- ✅ Fazer Inscrição em Eventos (apenas para si mesmo)
- ✅ Visualizar Meus Certificados
- ❌ Cadastro de Usuários
- ❌ Cadastro de Eventos
- ❌ Gerenciar inscrições de outros
- ❌ Emitir Certificados

## Fluxo de Autenticação

1. **Página Inicial**: Usuários não autenticados são redirecionados para a tela de login
2. **Login**: Usuário informa credenciais (username e senha)
3. **Dashboard**: Após login bem-sucedido, usuário é redirecionado ao dashboard personalizado
4. **Navegação**: Menu exibe apenas opções permitidas para o perfil do usuário
5. **Logout**: Usuário pode sair a qualquer momento

## Estrutura de URLs

```
/                          → Redireciona para login (se não autenticado)
/login/                    → Tela de autenticação
/logout/                   → Logout do usuário
/dashboard/                → Dashboard personalizado (requer login)
/cadastro-usuarios/        → Cadastro de usuários (apenas ADMIN)
/cadastro-eventos/         → Cadastro de eventos (ADMIN, ORGANIZADOR)
/inscricao/                → Inscrição em eventos (todos autenticados)
/certificados/             → Certificados (todos autenticados, visualização customizada)
```

## Usuários de Teste

Execute o script para criar usuários de teste:

```bash
python manage.py shell < create_test_users.py
```

### Credenciais de Teste:

| Perfil      | Username     | Senha     |
|-------------|--------------|-----------|
| Admin       | admin        | admin123  |
| Organizador | organizador  | org123    |
| Aluno       | aluno        | aluno123  |
| Professor   | professor    | prof123   |

## Funcionalidades por Perfil

### Inscrição em Eventos

**ALUNO/PROFESSOR:**
- Interface simplificada: apenas seleciona o evento
- Sistema automaticamente registra a inscrição para o usuário logado
- Status inicial: PENDENTE
- Aguarda confirmação do organizador

**ADMIN/ORGANIZADOR:**
- Interface completa: seleciona evento, participante, status e presença
- Pode gerenciar inscrições de qualquer usuário
- Pode confirmar presença e alterar status

### Certificados

**ALUNO/PROFESSOR:**
- Visualiza lista de certificados recebidos
- Informações: evento, data, carga horária, emissor
- Opção para baixar PDF (futura implementação)

**ADMIN/ORGANIZADOR:**
- Formulário para emitir novos certificados
- Seleciona inscrição elegível (confirmada com presença)
- Define carga horária, validade e observações

## Decorators de Controle de Acesso

```python
@admin_required                           # Apenas ADMIN
@organizador_or_admin_required           # ADMIN ou ORGANIZADOR
@aluno_professor_required                # ALUNO ou PROFESSOR
@perfil_required(PerfilChoices.ADMIN)    # Customizado
@login_required(login_url='login')       # Qualquer usuário autenticado
```

## Navegação Dinâmica

O menu de navegação é renderizado dinamicamente baseado no perfil do usuário:

```django
{% if request.user.perfil == 'ADMIN' %}
    <!-- Exibe todas as opções -->
{% elif request.user.perfil == 'ORGANIZADOR' %}
    <!-- Exibe opções de gestão -->
{% elif request.user.perfil == 'ALUNO' or request.user.perfil == 'PROFESSOR' %}
    <!-- Exibe opções de participação -->
{% endif %}
```

## Mensagens de Feedback

O sistema utiliza Django Messages para feedback ao usuário:
- ✅ Sucesso: Login bem-sucedido, operações concluídas
- ❌ Erro: Credenciais inválidas, permissões negadas
- ℹ️ Info: Informações contextuais

## Segurança

- ✅ Autenticação obrigatória em todas as rotas (exceto login)
- ✅ Validação de perfil antes de processar requisições
- ✅ Redirecionamento automático para dashboard após login
- ✅ Mensagens de erro contextuais
- ✅ Proteção contra acesso não autorizado

## API REST

A API REST continua disponível com autenticação via Token:

1. Obter token: `POST /api-token-auth/` com username e password
2. Usar token: Header `Authorization: Token <seu_token>`
3. Listar eventos: `GET /api/eventos/`
4. Fazer inscrição: `POST /api/inscricao/` com `{"evento": <id>}`

## Próximos Passos

- [ ] Implementar geração de PDF para certificados
- [ ] Adicionar página de perfil do usuário
- [ ] Implementar recuperação de senha
- [ ] Adicionar dashboard com estatísticas
- [ ] Implementar notificações por email
