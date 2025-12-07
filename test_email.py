import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_eventos.settings')
django.setup()

def test_email():
    print(f"Testing email configuration...")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    
    try:
        send_mail(
            subject='Teste de Configuração de Email AEGS',
            message='Se você recebeu este email, a configuração SMTP do Django está funcionando corretamente.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER], # Send to self to test
            fail_silently=False,
        )
        print("✅ Email enviado com sucesso!")
    except Exception as e:
        print(f"❌ Falha ao enviar email: {e}")

if __name__ == "__main__":
    test_email()
