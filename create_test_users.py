"""
Script to create test users for different profiles.
Run with: python manage.py shell < create_test_users.py
"""
from api.models import Usuario, PerfilChoices, InstituicaoChoices

# Create ADMIN user
admin, created = Usuario.objects.get_or_create(
    username='admin',
    defaults={
        'nome': 'Administrador do Sistema',
        'email': 'admin@sgea.local',
        'telefone': '(61) 99999-0001',
        'perfil': PerfilChoices.ADMIN,
    }
)
if created:
    admin.set_password('Admin@123')
    admin.save()
    print(f"✓ ADMIN criado: {admin.username}")
else:
    # Update password if user exists
    admin.set_password('Admin@123')
    admin.save()
    print(f"  ADMIN atualizado: {admin.username}")

# Create ORGANIZADOR user
organizador, created = Usuario.objects.get_or_create(
    username='organizador',
    defaults={
        'nome': 'Maria Silva Organizadora',
        'email': 'organizador@sgea.com',
        'telefone': '(61) 99999-0002',
        'perfil': PerfilChoices.ORGANIZADOR,
    }
)
if created:
    organizador.set_password('Organizador@123')
    organizador.save()
    print(f"✓ ORGANIZADOR criado: {organizador.username}")
else:
    organizador.email = 'organizador@sgea.com'
    organizador.set_password('Organizador@123')
    organizador.save()
    print(f"  ORGANIZADOR atualizado: {organizador.username}")

# Create ALUNO user
aluno, created = Usuario.objects.get_or_create(
    username='aluno',
    defaults={
        'nome': 'João Santos Aluno',
        'email': 'aluno@sgea.com',
        'telefone': '(61) 99999-0003',
        'perfil': PerfilChoices.ALUNO,
        'instituicao': InstituicaoChoices.UNB,
    }
)
if created:
    aluno.set_password('Aluno@123')
    aluno.save()
    print(f"✓ ALUNO criado: {aluno.username}")
else:
    aluno.email = 'aluno@sgea.com'
    aluno.set_password('Aluno@123')
    aluno.save()
    print(f"  ALUNO atualizado: {aluno.username}")

# Create PROFESSOR user
professor, created = Usuario.objects.get_or_create(
    username='professor',
    defaults={
        'nome': 'Ana Costa Professora',
        'email': 'professor@sgea.com',
        'telefone': '(61) 99999-0004',
        'perfil': PerfilChoices.PROFESSOR,
        'instituicao': InstituicaoChoices.UNB,
    }
)
if created:
    professor.set_password('Professor@123')
    professor.save()
    print(f"✓ PROFESSOR criado: {professor.username}")
else:
    professor.email = 'professor@sgea.com'
    professor.set_password('Professor@123')
    professor.save()
    print(f"  PROFESSOR atualizado: {professor.username}")

print("\n=== Usuários de teste criados/atualizados ===")
print("Admin:       username='admin'       password='Admin@123'")
print("Organizador: username='organizador' password='Organizador@123'")
print("Aluno:       username='aluno'       password='Aluno@123'")
print("Professor:   username='professor'   password='Professor@123'")
