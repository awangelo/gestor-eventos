from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Usuario, Evento, Inscricao, Certificado, AcaoAuditoriaChoices
from .audit import log_action

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(
        acao=AcaoAuditoriaChoices.LOGIN,
        request=request,
        usuario=user,
        descricao=f"Usuário {user.username} realizou login."
    )

@receiver(post_save, sender=Usuario)
def log_user_creation(sender, instance, created, **kwargs):
    if created:
        # Note: We might not have the 'request' here to get the creator if created via shell/admin without request context easily.
        # But for traceability of "New User Created", this is good.
        # If created via Signup View, we might want to log there to capture IP.
        # However, signal ensures we catch all creations.
        log_action(
            acao=AcaoAuditoriaChoices.USUARIO_CRIADO,
            usuario_afetado=instance,
            descricao=f"Novo usuário criado: {instance.username} ({instance.perfil})"
        )

@receiver(post_save, sender=Evento)
def log_evento_save(sender, instance, created, **kwargs):
    acao = AcaoAuditoriaChoices.EVENTO_CRIADO if created else AcaoAuditoriaChoices.EVENTO_ATUALIZADO
    log_action(
        acao=acao,
        evento=instance,
        descricao=f"Evento '{instance.titulo}' {'criado' if created else 'atualizado'}."
    )

@receiver(post_save, sender=Inscricao)
def log_inscricao_save(sender, instance, created, **kwargs):
    if created:
        log_action(
            acao=AcaoAuditoriaChoices.INSCRICAO_CRIADA,
            inscricao=instance,
            usuario_afetado=instance.participante,
            evento=instance.evento,
            descricao=f"Inscrição realizada para {instance.participante.nome} no evento {instance.evento.titulo}"
        )
    else:
        # Log status changes if needed, or generic update
        log_action(
            acao=AcaoAuditoriaChoices.INSCRICAO_ATUALIZADA,
            inscricao=instance,
            usuario_afetado=instance.participante,
            evento=instance.evento,
            descricao=f"Inscrição atualizada para {instance.participante.nome} no evento {instance.evento.titulo}. Status: {instance.status}"
        )

@receiver(post_save, sender=Certificado)
def log_certificado_save(sender, instance, created, **kwargs):
    if created:
        log_action(
            acao=AcaoAuditoriaChoices.CERTIFICADO_GERADO,
            certificado=instance,
            usuario_afetado=instance.inscricao.participante,
            evento=instance.inscricao.evento,
            descricao=f"Certificado gerado para {instance.inscricao.participante.nome} no evento {instance.inscricao.evento.titulo}"
        )
