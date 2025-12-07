from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from api.models import Evento, Inscricao, Certificado, InscricaoStatus

class Command(BaseCommand):
    help = 'Emite certificados automaticamente para eventos finalizados e notifica por e-mail'

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        
        # Buscar eventos que já terminaram (data_fim < hoje)
        eventos_finalizados = Evento.objects.filter(data_fim__lt=hoje)
        
        count_emitidos = 0
        
        for evento in eventos_finalizados:
            # Buscar inscrições confirmadas e com presença confirmada
            inscricoes_aptas = Inscricao.objects.filter(
                evento=evento,
                status=InscricaoStatus.CONFIRMADA,
                presenca_confirmada=True
            )
            
            for inscricao in inscricoes_aptas:
                # Verificar se já existe certificado
                if not hasattr(inscricao, 'certificado'):
                    cert = Certificado.objects.create(
                        inscricao=inscricao,
                        carga_horaria=evento.carga_horaria,
                        # emitido_por pode ficar null (sistema) ou definir um usuário padrão
                    )
                    count_emitidos += 1
                    self.stdout.write(self.style.SUCCESS(f'Certificado emitido para {inscricao.participante} no evento {evento}'))

                    # Enviar e-mail de notificação
                    try:
                        destinatario = inscricao.participante.email.strip()
                        if not destinatario:
                            raise ValueError("E-mail do participante está vazio.")

                        self.stdout.write(f'  - Tentando enviar para: {destinatario} via {settings.EMAIL_BACKEND}...')

                        nome_evento = evento.titulo if evento.titulo else str(evento)
                        subject = f'Certificado Disponível: {nome_evento}'
                        message = (
                            f'Olá {inscricao.participante.nome},\n\n'
                            f'Seu certificado para o evento "{nome_evento}" já foi emitido e está disponível no sistema.\n'
                            f'Acesse o portal para fazer o download.\n\n'
                            f'Atenciosamente,\n'
                            f'Equipe AEGS'
                        )
                        
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [destinatario],
                            fail_silently=False,
                        )
                        self.stdout.write(self.style.SUCCESS(f'  - E-mail ENVIADO COM SUCESSO para {destinatario}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  - FALHA ao enviar e-mail para {inscricao.participante.email}: {e}'))
                        import traceback
                        self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
        if count_emitidos > 0:
            self.stdout.write(self.style.SUCCESS(f'Total de certificados emitidos: {count_emitidos}'))
        else:
            self.stdout.write(self.style.WARNING('Nenhum novo certificado para emitir.'))
