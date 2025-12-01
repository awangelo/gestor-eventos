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
    admin.set_password('admin123')
    admin.save()
    print(f"✓ ADMIN criado: {admin.username}")
else:
    print(f"  ADMIN já existe: {admin.username}")

# Create ORGANIZADOR user
organizador, created = Usuario.objects.get_or_create(
    username='organizador',
    defaults={
        'nome': 'Maria Silva Organizadora',
        'email': 'organizador@sgea.local',
        'telefone': '(61) 99999-0002',
        'perfil': PerfilChoices.ORGANIZADOR,
    }
)
if created:
    organizador.set_password('org123')
    organizador.save()
    print(f"✓ ORGANIZADOR criado: {organizador.username}")
else:
    print(f"  ORGANIZADOR já existe: {organizador.username}")

# Create ALUNO user
aluno, created = Usuario.objects.get_or_create(
    username='aluno',
    defaults={
        'nome': 'João Santos Aluno',
        'email': 'aluno@sgea.local',
        'telefone': '(61) 99999-0003',
        'perfil': PerfilChoices.ALUNO,
        'instituicao': InstituicaoChoices.UNB,
    }
)
if created:
    aluno.set_password('aluno123')
    aluno.save()
    print(f"✓ ALUNO criado: {aluno.username}")
else:
    print(f"  ALUNO já existe: {aluno.username}")

# Create PROFESSOR user
professor, created = Usuario.objects.get_or_create(
    username='professor',
    defaults={
        'nome': 'Ana Costa Professora',
        'email': 'professor@sgea.local',
        'telefone': '(61) 99999-0004',
        'perfil': PerfilChoices.PROFESSOR,
        'instituicao': InstituicaoChoices.UNB,
    }
)
if created:
    professor.set_password('prof123')
    professor.save()
    print(f"✓ PROFESSOR criado: {professor.username}")
else:
    print(f"  PROFESSOR já existe: {professor.username}")

print("\n=== Usuários de teste criados ===")
print("Admin:       username='admin'       password='admin123'")
print("Organizador: username='organizador' password='org123'")
print("Aluno:       username='aluno'       password='aluno123'")
print("Professor:   username='professor'   password='prof123'")
