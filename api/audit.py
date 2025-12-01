"""
Audit logging utilities for tracking critical actions.
"""

from django.http import HttpRequest
from .models import AuditLog, AcaoAuditoriaChoices, Usuario, Evento, Inscricao, Certificado


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(
    acao: str,
    request: HttpRequest = None,
    usuario: Usuario = None,
    usuario_afetado: Usuario = None,
    evento: Evento = None,
    inscricao: Inscricao = None,
    certificado: Certificado = None,
    descricao: str = "",
    dados_extras: dict = None
):
    """
    Log an audit action.
    
    Args:
        acao: Action type from AcaoAuditoriaChoices
        request: HTTP request object (for IP and user agent)
        usuario: User who performed the action
        usuario_afetado: User affected by the action
        evento: Related event
        inscricao: Related inscricao
        certificado: Related certificado
        descricao: Detailed description
        dados_extras: Extra data as JSON
    """
    ip_address = None
    user_agent = ""
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        # If usuario not provided, get from request
        if not usuario and hasattr(request, 'user') and request.user.is_authenticated:
            usuario = request.user
    
    try:
        AuditLog.objects.create(
            acao=acao,
            usuario=usuario,
            usuario_afetado=usuario_afetado,
            evento=evento,
            inscricao=inscricao,
            certificado=certificado,
            descricao=descricao,
            ip_address=ip_address,
            user_agent=user_agent,
            dados_extras=dados_extras
        )
    except Exception as e:
        # Log errors but don't break the application
        print(f"Erro ao registrar auditoria: {e}")


# Convenience functions for specific actions

def log_usuario_criado(request, usuario_criado: Usuario, criado_por: Usuario = None):
    """Log user creation."""
    log_action(
        acao=AcaoAuditoriaChoices.USUARIO_CRIADO,
        request=request,
        usuario=criado_por,
        usuario_afetado=usuario_criado,
        descricao=f"Novo usuário '{usuario_criado.username}' ({usuario_criado.get_perfil_display()}) criado"
    )


def log_evento_criado(request, evento: Evento):
    """Log event creation."""
    log_action(
        acao=AcaoAuditoriaChoices.EVENTO_CRIADO,
        request=request,
        evento=evento,
        descricao=f"Evento '{evento.titulo or evento.get_tipo_display()}' criado",
        dados_extras={
            'tipo': evento.tipo,
            'local': evento.local,
            'capacidade': evento.capacidade,
            'data_inicio': evento.data_inicio.isoformat(),
        }
    )


def log_evento_atualizado(request, evento: Evento, campos_alterados: list = None):
    """Log event update."""
    log_action(
        acao=AcaoAuditoriaChoices.EVENTO_ATUALIZADO,
        request=request,
        evento=evento,
        descricao=f"Evento '{evento.titulo or evento.get_tipo_display()}' atualizado",
        dados_extras={'campos_alterados': campos_alterados} if campos_alterados else None
    )


def log_evento_excluido(request, evento_info: dict):
    """Log event deletion."""
    log_action(
        acao=AcaoAuditoriaChoices.EVENTO_EXCLUIDO,
        request=request,
        descricao=f"Evento '{evento_info.get('titulo', evento_info.get('tipo'))}' excluído",
        dados_extras=evento_info
    )


def log_evento_consultado_api(request, evento: Evento = None):
    """Log API event query."""
    descricao = f"Consulta de evento via API: {evento.titulo or evento.get_tipo_display()}" if evento else "Consulta de lista de eventos via API"
    log_action(
        acao=AcaoAuditoriaChoices.EVENTO_CONSULTADO_API,
        request=request,
        evento=evento,
        descricao=descricao
    )


def log_inscricao_criada(request, inscricao: Inscricao):
    """Log inscricao creation."""
    log_action(
        acao=AcaoAuditoriaChoices.INSCRICAO_CRIADA,
        request=request,
        usuario_afetado=inscricao.participante,
        evento=inscricao.evento,
        inscricao=inscricao,
        descricao=f"Inscrição de '{inscricao.participante.nome}' no evento '{inscricao.evento.titulo or inscricao.evento.get_tipo_display()}'",
        dados_extras={'status': inscricao.status}
    )


def log_inscricao_atualizada(request, inscricao: Inscricao, status_anterior: str = None):
    """Log inscricao update."""
    descricao = f"Inscrição de '{inscricao.participante.nome}' atualizada"
    if status_anterior:
        descricao += f" (status: {status_anterior} → {inscricao.get_status_display()})"
    
    log_action(
        acao=AcaoAuditoriaChoices.INSCRICAO_ATUALIZADA,
        request=request,
        usuario_afetado=inscricao.participante,
        evento=inscricao.evento,
        inscricao=inscricao,
        descricao=descricao,
        dados_extras={
            'status_anterior': status_anterior,
            'status_novo': inscricao.status
        }
    )


def log_inscricao_cancelada(request, inscricao: Inscricao):
    """Log inscricao cancellation."""
    log_action(
        acao=AcaoAuditoriaChoices.INSCRICAO_CANCELADA,
        request=request,
        usuario_afetado=inscricao.participante,
        evento=inscricao.evento,
        inscricao=inscricao,
        descricao=f"Inscrição de '{inscricao.participante.nome}' cancelada no evento '{inscricao.evento.titulo or inscricao.evento.get_tipo_display()}'"
    )


def log_certificado_gerado(request, certificado: Certificado):
    """Log certificate generation."""
    log_action(
        acao=AcaoAuditoriaChoices.CERTIFICADO_GERADO,
        request=request,
        usuario_afetado=certificado.inscricao.participante,
        evento=certificado.inscricao.evento,
        certificado=certificado,
        descricao=f"Certificado gerado para '{certificado.inscricao.participante.nome}' - Código: {certificado.codigo}",
        dados_extras={
            'codigo': str(certificado.codigo),
            'carga_horaria': certificado.carga_horaria
        }
    )


def log_certificado_consultado(request, certificado: Certificado, via_api: bool = False):
    """Log certificate query."""
    acao = AcaoAuditoriaChoices.CERTIFICADO_CONSULTADO_API if via_api else AcaoAuditoriaChoices.CERTIFICADO_CONSULTADO
    
    log_action(
        acao=acao,
        request=request,
        usuario_afetado=certificado.inscricao.participante,
        certificado=certificado,
        descricao=f"Certificado {certificado.codigo} consultado" + (" via API" if via_api else ""),
        dados_extras={'codigo': str(certificado.codigo)}
    )


def log_login(request, usuario: Usuario):
    """Log user login."""
    log_action(
        acao=AcaoAuditoriaChoices.LOGIN,
        request=request,
        usuario=usuario,
        descricao=f"Login do usuário '{usuario.username}'"
    )


def log_logout(request, usuario: Usuario):
    """Log user logout."""
    log_action(
        acao=AcaoAuditoriaChoices.LOGOUT,
        request=request,
        usuario=usuario,
        descricao=f"Logout do usuário '{usuario.username}'"
    )
