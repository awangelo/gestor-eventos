from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def enviar_email_boas_vindas(usuario):
    """
    Envia e-mail de boas-vindas para o novo usuário.
    """
    assunto = 'Bem-vindo ao AEGS!'
    mensagem = f"""
    Olá, {usuario.nome}!
    
    Seja bem-vindo ao AEGS.
    Sua conta foi criada com sucesso.
    
    Agora você pode se inscrever em eventos e gerenciar suas participações.
    
    Atenciosamente,
    Equipe AEGS
    """
    
    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Erro ao enviar email de boas-vindas: {e}")

def enviar_email_inscricao(inscricao):
    """
    Envia e-mail de confirmação de inscrição.
    """
    evento = inscricao.evento
    usuario = inscricao.participante
    
    assunto = f'Inscrição Confirmada: {evento.titulo or evento.get_tipo_display()}'
    mensagem = f"""
    Olá, {usuario.nome}!
    
    Sua inscrição no evento "{evento.titulo or evento.get_tipo_display()}" foi realizada com sucesso.
    
    Detalhes do Evento:
    Data: {evento.data_inicio.strftime('%d/%m/%Y')}
    Horário: {evento.horario.strftime('%H:%M') if evento.horario else 'A definir'}
    Local: {evento.local}
    
    Status da Inscrição: {inscricao.get_status_display()}
    
    Não se esqueça de comparecer!
    
    Atenciosamente,
    Equipe AEGS
    """
    
    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Erro ao enviar email de inscrição: {e}")

def enviar_email_certificado(certificado):
    """
    Envia e-mail com o certificado.
    """
    inscricao = certificado.inscricao
    usuario = inscricao.participante
    evento = inscricao.evento
    
    assunto = f'Certificado Disponível: {evento.titulo or evento.get_tipo_display()}'
    mensagem = f"""
    Olá, {usuario.nome}!
    
    O certificado de sua participação no evento "{evento.titulo or evento.get_tipo_display()}" já está disponível.
    
    Carga Horária: {certificado.carga_horaria} horas
    
    Você pode visualizar e imprimir seu certificado acessando a área "Meus Eventos" no sistema.
    
    Parabéns pela participação!
    
    Atenciosamente,
    Equipe AEGS
    """
    
    try:
        print(f"Tentando enviar email de certificado para {usuario.email}...")
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        print(f"Email de certificado enviado com sucesso para {usuario.email}")
    except Exception as e:
        print(f"ERRO CRÍTICO ao enviar email de certificado: {e}")
        # Re-raise para que a view possa saber que falhou, se necessário, 
        # ou pelo menos para garantir que o erro apareça nos logs do servidor.
        raise e
