#!/usr/bin/env python
"""
Script para popular o banco de dados com dados de exemplo completos.
Cobre todas as operações do sistema: usuários, eventos, inscrições, presenças e certificados.
"""

import os
import sys
import django
from datetime import date, time, timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_eventos.settings')
django.setup()

from api.models import (
    Usuario, Evento, Inscricao, Certificado,
    PerfilChoices, InstituicaoChoices, TipoEventoChoices, InscricaoStatus
)
from django.db import transaction


def limpar_dados():
    """Remove todos os dados existentes."""
    print("\n" + "="*70)
    print(" LIMPANDO DADOS EXISTENTES")
    print("="*70)
    
    with transaction.atomic():
        # Ordem importa devido às foreign keys
        count_certs = Certificado.objects.all().delete()[0]
        count_inscr = Inscricao.objects.all().delete()[0]
        count_eventos = Evento.objects.all().delete()[0]
        count_users = Usuario.objects.all().delete()[0]
        
        print(f"✓ {count_certs} certificados removidos")
        print(f"✓ {count_inscr} inscrições removidas")
        print(f"✓ {count_eventos} eventos removidos")
        print(f"✓ {count_users} usuários removidos")


def criar_usuarios():
    """Cria usuários de exemplo para todos os perfis."""
    print("\n" + "="*70)
    print(" CRIANDO USUÁRIOS")
    print("="*70)
    
    usuarios = []
    
    # 1 ADMIN
    admin = Usuario.objects.create_user(
        username='admin',
        password='admin123!',
        email='admin@aegs.edu.br',
        nome='Administrador do Sistema',
        telefone='(61) 99999-0000',
        perfil=PerfilChoices.ADMIN,
        is_staff=True,
        is_superuser=True
    )
    usuarios.append(admin)
    print(f"✓ ADMIN criado: {admin.username}")
    
    # 2 ORGANIZADORES
    org1 = Usuario.objects.create_user(
        username='carlos.org',
        password='org123!',
        email='carlos@aegs.edu.br',
        nome='Carlos Eduardo Silva',
        telefone='(61) 98888-1111',
        perfil=PerfilChoices.ORGANIZADOR
    )
    usuarios.append(org1)
    print(f"✓ ORGANIZADOR criado: {org1.username}")
    
    org2 = Usuario.objects.create_user(
        username='ana.organizadora',
        password='org456!',
        email='ana.org@aegs.edu.br',
        nome='Ana Paula Santos',
        telefone='(61) 98888-2222',
        perfil=PerfilChoices.ORGANIZADOR
    )
    usuarios.append(org2)
    print(f"✓ ORGANIZADOR criado: {org2.username}")
    
    # 3 PROFESSORES
    prof1 = Usuario.objects.create_user(
        username='maria.prof',
        password='prof123!',
        email='maria@unb.br',
        nome='Maria Oliveira Costa',
        telefone='(61) 97777-3333',
        perfil=PerfilChoices.PROFESSOR,
        instituicao=InstituicaoChoices.UNB
    )
    usuarios.append(prof1)
    print(f"✓ PROFESSOR criado: {prof1.username}")
    
    prof2 = Usuario.objects.create_user(
        username='joao.professor',
        password='prof456!',
        email='joao@ifb.edu.br',
        nome='João Pedro Almeida',
        telefone='(61) 97777-4444',
        perfil=PerfilChoices.PROFESSOR,
        instituicao=InstituicaoChoices.IFB
    )
    usuarios.append(prof2)
    print(f"✓ PROFESSOR criado: {prof2.username}")
    
    prof3 = Usuario.objects.create_user(
        username='patricia.prof',
        password='prof789!',
        email='patricia@ceub.br',
        nome='Patrícia Rodrigues Lima',
        telefone='(61) 97777-5555',
        perfil=PerfilChoices.PROFESSOR,
        instituicao=InstituicaoChoices.CEUB
    )
    usuarios.append(prof3)
    print(f"✓ PROFESSOR criado: {prof3.username}")
    
    # 8 ALUNOS
    alunos_data = [
        ('bruno.aluno', 'Bruno Henrique Souza', 'bruno@aluno.unb.br', InstituicaoChoices.UNB, '(61) 96666-1111'),
        ('julia.aluna', 'Júlia Fernandes Lima', 'julia@aluno.unb.br', InstituicaoChoices.UNB, '(61) 96666-2222'),
        ('rafael.estudante', 'Rafael Costa Santos', 'rafael@estudante.ifb.edu.br', InstituicaoChoices.IFB, '(61) 96666-3333'),
        ('camila.aluna', 'Camila Pereira Silva', 'camila@aluna.ceub.br', InstituicaoChoices.CEUB, '(61) 96666-4444'),
        ('lucas.aluno', 'Lucas Gabriel Martins', 'lucas@aluno.iesb.br', InstituicaoChoices.IESB, '(61) 96666-5555'),
        ('fernanda.aluna', 'Fernanda Beatriz Rocha', 'fernanda@aluna.ucb.br', InstituicaoChoices.UCB, '(61) 96666-6666'),
        ('pedro.aluno', 'Pedro Augusto Oliveira', 'pedro@aluno.unb.br', InstituicaoChoices.UNB, '(61) 96666-7777'),
        ('mariana.aluna', 'Mariana Silva Costa', 'mariana@aluna.ifb.edu.br', InstituicaoChoices.IFB, '(61) 96666-8888'),
    ]
    
    for username, nome, email, instituicao, telefone in alunos_data:
        aluno = Usuario.objects.create_user(
            username=username,
            password='aluno123!',
            email=email,
            nome=nome,
            telefone=telefone,
            perfil=PerfilChoices.ALUNO,
            instituicao=instituicao
        )
        usuarios.append(aluno)
        print(f"✓ ALUNO criado: {aluno.username}")
    
    print(f"\n✓ Total: {len(usuarios)} usuários criados")
    return usuarios


def criar_eventos(usuarios):
    """Cria eventos de exemplo de todos os tipos."""
    print("\n" + "="*70)
    print(" CRIANDO EVENTOS")
    print("="*70)
    
    # Buscar organizadores e professores
    org1 = Usuario.objects.get(username='carlos.org')
    org2 = Usuario.objects.get(username='ana.organizadora')
    admin = Usuario.objects.get(username='admin')
    prof1 = Usuario.objects.get(username='maria.prof')
    prof2 = Usuario.objects.get(username='joao.professor')
    prof3 = Usuario.objects.get(username='patricia.prof')
    
    eventos = []
    hoje = date.today()
    
    # Evento 1: PALESTRA (passado, com inscrições e certificados)
    evento1 = Evento.objects.create(
        tipo=TipoEventoChoices.PALESTRA,
        titulo='Inteligência Artificial na Educação',
        data_inicio=hoje - timedelta(days=30),
        data_fim=hoje - timedelta(days=30),
        horario=time(14, 0),
        local='Auditório Central - UnB',
        capacidade=100,
        organizador=org1,
        professor_responsavel=prof1
    )
    eventos.append(evento1)
    print(f"✓ PALESTRA criada: {evento1.titulo}")
    
    # Evento 2: WORKSHOP (passado recente, com inscrições)
    evento2 = Evento.objects.create(
        tipo=TipoEventoChoices.WORKSHOP,
        titulo='Desenvolvimento Web com Django',
        data_inicio=hoje - timedelta(days=7),
        data_fim=hoje - timedelta(days=5),
        horario=time(9, 0),
        local='Laboratório de Informática - IFB',
        capacidade=30,
        organizador=org2,
        professor_responsavel=prof2
    )
    eventos.append(evento2)
    print(f"✓ WORKSHOP criado: {evento2.titulo}")
    
    # Evento 3: MINICURSO (em andamento)
    evento3 = Evento.objects.create(
        tipo=TipoEventoChoices.MINICURSO,
        titulo='Python para Análise de Dados',
        data_inicio=hoje - timedelta(days=2),
        data_fim=hoje + timedelta(days=3),
        horario=time(19, 0),
        local='Sala 301 - CEUB',
        capacidade=25,
        organizador=org1,
        professor_responsavel=prof3
    )
    eventos.append(evento3)
    print(f"✓ MINICURSO criado: {evento3.titulo}")
    
    # Evento 4: SEMINÁRIO (futuro próximo)
    evento4 = Evento.objects.create(
        tipo=TipoEventoChoices.SEMINARIO,
        titulo='Inovação e Tecnologia no Ensino Superior',
        data_inicio=hoje + timedelta(days=5),
        data_fim=hoje + timedelta(days=5),
        horario=time(10, 0),
        local='Centro de Convenções',
        capacidade=200,
        organizador=admin,
        professor_responsavel=prof1
    )
    eventos.append(evento4)
    print(f"✓ SEMINÁRIO criado: {evento4.titulo}")
    
    # Evento 5: PALESTRA (futuro)
    evento5 = Evento.objects.create(
        tipo=TipoEventoChoices.PALESTRA,
        titulo='Metodologias Ágeis em Projetos Acadêmicos',
        data_inicio=hoje + timedelta(days=15),
        data_fim=hoje + timedelta(days=15),
        horario=time(16, 0),
        local='Auditório - IESB',
        capacidade=80,
        organizador=org2,
        professor_responsavel=prof2
    )
    eventos.append(evento5)
    print(f"✓ PALESTRA criada: {evento5.titulo}")
    
    # Evento 6: WORKSHOP (futuro, quase lotado)
    evento6 = Evento.objects.create(
        tipo=TipoEventoChoices.WORKSHOP,
        titulo='Segurança da Informação e Privacidade',
        data_inicio=hoje + timedelta(days=20),
        data_fim=hoje + timedelta(days=21),
        horario=time(14, 0),
        local='Lab. Segurança - UnB',
        capacidade=20,
        organizador=org1,
        professor_responsavel=prof3
    )
    eventos.append(evento6)
    print(f"✓ WORKSHOP criado: {evento6.titulo}")
    
    # Evento 7: OUTRO (futuro distante)
    evento7 = Evento.objects.create(
        tipo=TipoEventoChoices.OUTRO,
        titulo='Hackathon Acadêmico 2025',
        data_inicio=hoje + timedelta(days=60),
        data_fim=hoje + timedelta(days=62),
        horario=time(8, 0),
        local='Campus Tecnológico',
        capacidade=50,
        organizador=admin,
        professor_responsavel=prof1
    )
    eventos.append(evento7)
    print(f"✓ OUTRO evento criado: {evento7.titulo}")
    
    print(f"\n✓ Total: {len(eventos)} eventos criados")
    return eventos


def criar_inscricoes(usuarios, eventos):
    """Cria inscrições de exemplo com diferentes status."""
    print("\n" + "="*70)
    print(" CRIANDO INSCRIÇÕES")
    print("="*70)
    
    # Buscar alunos e professores
    alunos = Usuario.objects.filter(perfil=PerfilChoices.ALUNO)
    professores = Usuario.objects.filter(perfil=PerfilChoices.PROFESSOR)
    
    inscricoes = []
    
    # Evento 1 (passado): 8 confirmadas com presença, 2 confirmadas sem presença, 1 cancelada
    evento1 = eventos[0]
    participantes_e1 = list(alunos[:8])
    
    for i, participante in enumerate(participantes_e1):
        inscricao = Inscricao.objects.create(
            evento=evento1,
            participante=participante,
            status=InscricaoStatus.CONFIRMADA,
            presenca_confirmada=True  # Primeiros 8 com presença
        )
        inscricoes.append(inscricao)
    
    # Mais 2 confirmadas sem presença
    inscricao = Inscricao.objects.create(
        evento=evento1,
        participante=professores[0],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False
    )
    inscricoes.append(inscricao)
    
    inscricao = Inscricao.objects.create(
        evento=evento1,
        participante=professores[1],
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=False
    )
    inscricoes.append(inscricao)
    
    # 1 cancelada
    inscricao = Inscricao.objects.create(
        evento=evento1,
        participante=professores[2],
        status=InscricaoStatus.CANCELADA,
        presenca_confirmada=False
    )
    inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento1.titulo}': 11 inscrições (8 confirmadas c/ presença, 2 confirmadas s/ presença, 1 cancelada)")
    
    # Evento 2 (passado recente): 5 confirmadas com presença, 3 pendentes
    evento2 = eventos[1]
    
    for participante in alunos[:5]:
        inscricao = Inscricao.objects.create(
            evento=evento2,
            participante=participante,
            status=InscricaoStatus.CONFIRMADA,
            presenca_confirmada=True
        )
        inscricoes.append(inscricao)
    
    for participante in alunos[5:8]:
        inscricao = Inscricao.objects.create(
            evento=evento2,
            participante=participante,
            status=InscricaoStatus.PENDENTE,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento2.titulo}': 8 inscrições (5 confirmadas c/ presença, 3 pendentes)")
    
    # Evento 3 (em andamento): 10 confirmadas, 2 pendentes
    evento3 = eventos[2]
    
    for participante in list(alunos[:6]) + list(professores[:4]):
        inscricao = Inscricao.objects.create(
            evento=evento3,
            participante=participante,
            status=InscricaoStatus.CONFIRMADA,
            presenca_confirmada=False  # Evento ainda em andamento
        )
        inscricoes.append(inscricao)
    
    for participante in alunos[6:8]:
        inscricao = Inscricao.objects.create(
            evento=evento3,
            participante=participante,
            status=InscricaoStatus.PENDENTE,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento3.titulo}': 12 inscrições (10 confirmadas, 2 pendentes)")
    
    # Evento 4 (futuro próximo): 15 confirmadas, 5 pendentes
    evento4 = eventos[3]
    
    todos_participantes = list(alunos) + list(professores)
    for participante in todos_participantes[:15]:
        inscricao = Inscricao.objects.create(
            evento=evento4,
            participante=participante,
            status=InscricaoStatus.CONFIRMADA,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    for i in range(5):
        if i < len(todos_participantes) - 15:
            inscricao = Inscricao.objects.create(
                evento=evento4,
                participante=todos_participantes[15 + i],
                status=InscricaoStatus.PENDENTE,
                presenca_confirmada=False
            )
            inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento4.titulo}': ~20 inscrições (15 confirmadas, 5 pendentes)")
    
    # Evento 5 (futuro): 6 confirmadas, 4 pendentes
    evento5 = eventos[4]
    
    for participante in alunos[:6]:
        inscricao = Inscricao.objects.create(
            evento=evento5,
            participante=participante,
            status=InscricaoStatus.CONFIRMADA,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    for participante in alunos[6:8]:
        inscricao = Inscricao.objects.create(
            evento=evento5,
            participante=participante,
            status=InscricaoStatus.PENDENTE,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    for participante in professores[:2]:
        inscricao = Inscricao.objects.create(
            evento=evento5,
            participante=participante,
            status=InscricaoStatus.PENDENTE,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento5.titulo}': 10 inscrições (6 confirmadas, 4 pendentes)")
    
    # Evento 6 (futuro, quase lotado): 18 confirmadas (capacidade 20)
    evento6 = eventos[5]
    
    participantes_e6 = list(alunos) + list(professores[:2])
    for participante in participantes_e6[:18]:
        inscricao = Inscricao.objects.create(
            evento=evento6,
            participante=participante,
            status=InscricaoStatus.CONFIRMADA,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento6.titulo}': 18 inscrições (18 confirmadas - quase lotado!)")
    
    # Evento 7 (futuro distante): 3 pendentes
    evento7 = eventos[6]
    
    for participante in alunos[:3]:
        inscricao = Inscricao.objects.create(
            evento=evento7,
            participante=participante,
            status=InscricaoStatus.PENDENTE,
            presenca_confirmada=False
        )
        inscricoes.append(inscricao)
    
    print(f"✓ Evento '{evento7.titulo}': 3 inscrições (3 pendentes)")
    
    print(f"\n✓ Total: {len(inscricoes)} inscrições criadas")
    return inscricoes


def criar_certificados():
    """Cria certificados para participantes com presença confirmada."""
    print("\n" + "="*70)
    print(" CRIANDO CERTIFICADOS")
    print("="*70)
    
    # Buscar organizadores
    org1 = Usuario.objects.get(username='carlos.org')
    org2 = Usuario.objects.get(username='ana.organizadora')
    admin = Usuario.objects.get(username='admin')
    
    # Certificados para evento 1 (8 participantes com presença)
    inscricoes_evento1 = Inscricao.objects.filter(
        evento__titulo='Inteligência Artificial na Educação',
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=True
    )
    
    certificados = []
    for inscricao in inscricoes_evento1:
        certificado = Certificado.objects.create(
            inscricao=inscricao,
            emitido_por=org1,
            carga_horaria=4,
            validade=date.today() + timedelta(days=730),  # 2 anos
            observacoes='Certificado de participação em palestra sobre IA na Educação.'
        )
        certificados.append(certificado)
    
    print(f"✓ {len(certificados)} certificados criados para evento 'Inteligência Artificial na Educação'")
    
    # Certificados para evento 2 (5 participantes com presença)
    inscricoes_evento2 = Inscricao.objects.filter(
        evento__titulo='Desenvolvimento Web com Django',
        status=InscricaoStatus.CONFIRMADA,
        presenca_confirmada=True
    )
    
    count = 0
    for inscricao in inscricoes_evento2:
        certificado = Certificado.objects.create(
            inscricao=inscricao,
            emitido_por=org2,
            carga_horaria=12,
            validade=date.today() + timedelta(days=730),
            observacoes='Certificado de participação em workshop de desenvolvimento web.'
        )
        certificados.append(certificado)
        count += 1
    
    print(f"✓ {count} certificados criados para evento 'Desenvolvimento Web com Django'")
    
    print(f"\n✓ Total: {len(certificados)} certificados emitidos")
    return certificados


def imprimir_resumo():
    """Imprime resumo dos dados criados."""
    print("\n" + "="*70)
    print(" RESUMO DOS DADOS CRIADOS")
    print("="*70)
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  • Usuários: {Usuario.objects.count()}")
    print(f"    - ADMIN: {Usuario.objects.filter(perfil=PerfilChoices.ADMIN).count()}")
    print(f"    - ORGANIZADOR: {Usuario.objects.filter(perfil=PerfilChoices.ORGANIZADOR).count()}")
    print(f"    - PROFESSOR: {Usuario.objects.filter(perfil=PerfilChoices.PROFESSOR).count()}")
    print(f"    - ALUNO: {Usuario.objects.filter(perfil=PerfilChoices.ALUNO).count()}")
    
    print(f"\n  • Eventos: {Evento.objects.count()}")
    print(f"    - PALESTRA: {Evento.objects.filter(tipo=TipoEventoChoices.PALESTRA).count()}")
    print(f"    - WORKSHOP: {Evento.objects.filter(tipo=TipoEventoChoices.WORKSHOP).count()}")
    print(f"    - MINICURSO: {Evento.objects.filter(tipo=TipoEventoChoices.MINICURSO).count()}")
    print(f"    - SEMINÁRIO: {Evento.objects.filter(tipo=TipoEventoChoices.SEMINARIO).count()}")
    print(f"    - OUTRO: {Evento.objects.filter(tipo=TipoEventoChoices.OUTRO).count()}")
    
    print(f"\n  • Inscrições: {Inscricao.objects.count()}")
    print(f"    - CONFIRMADA: {Inscricao.objects.filter(status=InscricaoStatus.CONFIRMADA).count()}")
    print(f"    - PENDENTE: {Inscricao.objects.filter(status=InscricaoStatus.PENDENTE).count()}")
    print(f"    - CANCELADA: {Inscricao.objects.filter(status=InscricaoStatus.CANCELADA).count()}")
    print(f"    - Com presença: {Inscricao.objects.filter(presenca_confirmada=True).count()}")
    
    print(f"\n  • Certificados: {Certificado.objects.count()}")
    
    print("\n" + "="*70)
    print(" CREDENCIAIS DE ACESSO")
    print("="*70)
    print("\n  ADMIN:")
    print("    username: admin")
    print("    password: admin123!")
    
    print("\n  ORGANIZADORES:")
    print("    username: carlos.org / password: org123!")
    print("    username: ana.organizadora / password: org456!")
    
    print("\n  PROFESSORES:")
    print("    username: maria.prof / password: prof123!")
    print("    username: joao.professor / password: prof456!")
    print("    username: patricia.prof / password: prof789!")
    
    print("\n  ALUNOS (todos com senha: aluno123!):")
    alunos = Usuario.objects.filter(perfil=PerfilChoices.ALUNO).order_by('username')
    for aluno in alunos:
        print(f"    username: {aluno.username}")
    
    print("\n" + "="*70)
    print(" ✅ BANCO DE DADOS POPULADO COM SUCESSO!")
    print("="*70)
    print()


def main():
    """Função principal."""
    print("\n" + "="*70)
    print(" SCRIPT DE POPULAÇÃO DO BANCO DE DADOS")
    print(" Sistema de Gestão de Eventos Acadêmicos (AEGS)")
    print("="*70)
    
    try:
        # 1. Limpar dados existentes
        limpar_dados()
        
        # 2. Criar usuários
        usuarios = criar_usuarios()
        
        # 3. Criar eventos
        eventos = criar_eventos(usuarios)
        
        # 4. Criar inscrições
        inscricoes = criar_inscricoes(usuarios, eventos)
        
        # 5. Criar certificados
        certificados = criar_certificados()
        
        # 6. Imprimir resumo
        imprimir_resumo()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
