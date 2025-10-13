#!/usr/bin/env python
"""
Script para popular o banco de dados com dados de exemplo para o SGEA.
Execute com: python database/load_sample_data.py
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_eventos.settings')
django.setup()

from api.models import (
    Usuario,
    Evento,
    Inscricao,
    Certificado,
    PerfilChoices,
    InstituicaoChoices,
    TipoEventoChoices,
    InscricaoStatus,
)


def limpar_dados():
    """Remove todos os dados existentes."""
    print("Limpando dados existentes...")
    Certificado.objects.all().delete()
    Inscricao.objects.all().delete()
    Evento.objects.all().delete()
    Usuario.objects.all().delete()
    print("Dados limpos.\n")


def criar_usuarios():
    """Cria usuários de exemplo com diferentes perfis."""
    print("Criando usuarios...")
    
    usuarios = []
    
    # Admin
    admin = Usuario.objects.create_user(
        username='admin',
        password='admin123',
        email='admin@sgea.local',
        nome='Administrador do Sistema',
        telefone='(61) 91111-1111',
        perfil=PerfilChoices.ADMIN,
        is_staff=True,
        is_superuser=True,
    )
    usuarios.append(admin)
    
    # Organizadores
    org1 = Usuario.objects.create_user(
        username='carlos.org',
        password='senha123',
        email='carlos@sgea.local',
        nome='Carlos Organizador',
        telefone='(61) 92222-2222',
        perfil=PerfilChoices.ORGANIZADOR,
    )
    usuarios.append(org1)
    
    org2 = Usuario.objects.create_user(
        username='julia.org',
        password='senha123',
        email='julia@sgea.local',
        nome='Julia Organizadora',
        telefone='(61) 93333-3333',
        perfil=PerfilChoices.ORGANIZADOR,
    )
    usuarios.append(org2)
    
    # Alunos
    aluno1 = Usuario.objects.create_user(
        username='bruno.aluno',
        password='senha123',
        email='bruno@sgea.local',
        nome='Bruno Aluno Silva',
        telefone='(61) 94444-4444',
        perfil=PerfilChoices.ALUNO,
        instituicao=InstituicaoChoices.UNB,
    )
    usuarios.append(aluno1)
    
    aluno2 = Usuario.objects.create_user(
        username='ana.aluna',
        password='senha123',
        email='ana@sgea.local',
        nome='Ana Paula Aluna',
        telefone='(61) 95555-5555',
        perfil=PerfilChoices.ALUNO,
        instituicao=InstituicaoChoices.IFB,
    )
    usuarios.append(aluno2)
    
    aluno3 = Usuario.objects.create_user(
        username='pedro.aluno',
        password='senha123',
        email='pedro@sgea.local',
        nome='Pedro Henrique Costa',
        telefone='(61) 96666-6666',
        perfil=PerfilChoices.ALUNO,
        instituicao=InstituicaoChoices.CEUB,
    )
    usuarios.append(aluno3)
    
    # Professores
    prof1 = Usuario.objects.create_user(
        username='maria.prof',
        password='senha123',
        email='maria@sgea.local',
        nome='Maria Professora Santos',
        telefone='(61) 97777-7777',
        perfil=PerfilChoices.PROFESSOR,
        instituicao=InstituicaoChoices.UNB,
    )
    usuarios.append(prof1)
    
    prof2 = Usuario.objects.create_user(
        username='joao.prof',
        password='senha123',
        email='joao@sgea.local',
        nome='João Professor Oliveira',
        telefone='(61) 98888-8888',
        perfil=PerfilChoices.PROFESSOR,
        instituicao=InstituicaoChoices.UCB,
    )
    usuarios.append(prof2)
    
    print(f"{len(usuarios)} usuarios criados.\n")
    return {u.username: u for u in usuarios}


def criar_eventos(usuarios):
    """Cria eventos de exemplo."""
    print("Criando eventos...")
    
    hoje = date.today()
    eventos = []
    
    # Evento passado
    evento1 = Evento.objects.create(
        tipo=TipoEventoChoices.PALESTRA,
        data_inicio=hoje - timedelta(days=10),
        data_fim=hoje - timedelta(days=10),
        local='Auditório Central',
        capacidade=200,
        organizador=usuarios['carlos.org'],
    )
    eventos.append(evento1)
    
    # Evento em andamento
    evento2 = Evento.objects.create(
        tipo=TipoEventoChoices.WORKSHOP,
        data_inicio=hoje - timedelta(days=1),
        data_fim=hoje + timedelta(days=1),
        local='Sala 301',
        capacidade=30,
        organizador=usuarios['julia.org'],
    )
    eventos.append(evento2)
    
    # Eventos futuros
    evento3 = Evento.objects.create(
        tipo=TipoEventoChoices.MINICURSO,
        data_inicio=hoje + timedelta(days=7),
        data_fim=hoje + timedelta(days=9),
        local='Laboratório 202',
        capacidade=25,
        organizador=usuarios['carlos.org'],
    )
    eventos.append(evento3)
    
    evento4 = Evento.objects.create(
        tipo=TipoEventoChoices.SEMINARIO,
        data_inicio=hoje + timedelta(days=15),
        data_fim=hoje + timedelta(days=17),
        local='Auditório Norte',
        capacidade=150,
        organizador=usuarios['julia.org'],
    )
    eventos.append(evento4)
    
    evento5 = Evento.objects.create(
        tipo=TipoEventoChoices.PALESTRA,
        data_inicio=hoje + timedelta(days=30),
        data_fim=hoje + timedelta(days=30),
        local='Sala de Conferências',
        capacidade=100,
        organizador=usuarios['carlos.org'],
    )
    eventos.append(evento5)
    
    # Evento com capacidade baixa para testar limite
    evento6 = Evento.objects.create(
        tipo=TipoEventoChoices.WORKSHOP,
        data_inicio=hoje + timedelta(days=20),
        data_fim=hoje + timedelta(days=21),
        local='Sala Pequena',
        capacidade=5,
        organizador=usuarios['julia.org'],
    )
    eventos.append(evento6)
    
    print(f"{len(eventos)} eventos criados.\n")
    return eventos


def criar_inscricoes(eventos, usuarios):
    """Cria inscrições de exemplo."""
    print("Criando inscricoes...")
    
    inscricoes = []
    
    # Evento 1 (passado) - inscrições confirmadas com presença
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[0],
        participante=usuarios['bruno.aluno'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=True,
    ))
    
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[0],
        participante=usuarios['maria.prof'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=True,
    ))
    
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[0],
        participante=usuarios['ana.aluna'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False,
    ))
    
    # Evento 2 (em andamento) - mix de status
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[1],
        participante=usuarios['pedro.aluno'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=True,
    ))
    
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[1],
        participante=usuarios['joao.prof'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False,
    ))
    
    # Evento 3 (futuro) - pendentes e confirmadas
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[2],
        participante=usuarios['bruno.aluno'],
        status=InscricaoStatus.PENDENTE,
        presenca_confirmada=False,
    ))
    
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[2],
        participante=usuarios['ana.aluna'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False,
    ))
    
    # Evento 4 (futuro) - várias inscrições
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[3],
        participante=usuarios['maria.prof'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False,
    ))
    
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[3],
        participante=usuarios['pedro.aluno'],
        status=InscricaoStatus.PENDENTE,
        presenca_confirmada=False,
    ))
    
    # Evento 6 (capacidade baixa) - testar limite
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[5],
        participante=usuarios['bruno.aluno'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False,
    ))
    
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[5],
        participante=usuarios['ana.aluna'],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False,
    ))
    
    # Inscrição cancelada
    inscricoes.append(Inscricao.objects.create(
        evento=eventos[4],
        participante=usuarios['joao.prof'],
        status=InscricaoStatus.CANCELADA,
        presenca_confirmada=False,
    ))
    
    print(f"{len(inscricoes)} inscricoes criadas.\n")
    return inscricoes


def criar_certificados(inscricoes, usuarios):
    """Cria certificados para inscrições elegíveis."""
    print("Criando certificados...")
    
    certificados = []
    
    # Certificados para inscrições com presença confirmada
    inscricoes_elegiveis = [i for i in inscricoes if i.status == InscricaoStatus.CONFIRMADA and i.presenca_confirmada]
    
    for inscricao in inscricoes_elegiveis:
        # Determinar emissor (organizador do evento)
        emissor = inscricao.evento.organizador
        
        # Calcular carga horária baseada na duração do evento
        dias = (inscricao.evento.data_fim - inscricao.evento.data_inicio).days + 1
        carga_horaria = dias * 4  # 4 horas por dia
        
        cert = Certificado.objects.create(
            inscricao=inscricao,
            emitido_por=emissor,
            carga_horaria=carga_horaria,
            validade=inscricao.evento.data_fim + timedelta(days=365),  # 1 ano
            observacoes=f"Participação confirmada em {inscricao.evento.get_tipo_display()}.",
        )
        certificados.append(cert)
    
    print(f"{len(certificados)} certificados emitidos.\n")
    return certificados


def main():
    """Função principal para popular o banco de dados."""
    print("\nSGEA - Carregamento de Dados de Exemplo")
    print("=" * 60 + "\n")
    
    try:
        # Limpar dados existentes
        limpar_dados()
        
        # Criar dados
        usuarios = criar_usuarios()
        eventos = criar_eventos(usuarios)
        inscricoes = criar_inscricoes(eventos, usuarios)
        certificados = criar_certificados(inscricoes, usuarios)
        
        # Resumo
        print("=" * 60)
        print("DADOS CARREGADOS COM SUCESSO")
        print("=" * 60)
        print(f"\nResumo:")
        print(f"  - {Usuario.objects.count()} usuarios")
        print(f"  - {Evento.objects.count()} eventos")
        print(f"  - {Inscricao.objects.count()} inscricoes")
        print(f"  - {Certificado.objects.count()} certificados emitidos")
        
        print("\nCredenciais de acesso:")
        print("  - Admin: admin / admin123")
        print("  - Organizador: carlos.org / senha123")
        print("  - Organizador: julia.org / senha123")
        print("  - Aluno: bruno.aluno / senha123")
        print("  - Aluno: ana.aluna / senha123")
        print("  - Professor: maria.prof / senha123")
        
        print("\nExecute: python manage.py runserver")
        print("Acesse: http://127.0.0.1:8000/\n")
        
    except Exception as e:
        print(f"\nERRO ao carregar dados: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
