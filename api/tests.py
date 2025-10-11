from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
	Certificado,
	Evento,
	Inscricao,
	InscricaoStatus,
	PerfilChoices,
	TipoEventoChoices,
	Usuario,
)


class ModeloTestCase(TestCase):
	def setUp(self):
		self.organizador = Usuario.objects.create_user(
			username="organizer",
			password="SenhaSegura!1",
			nome="Organizador Chefe",
			telefone="61999990000",
			perfil=PerfilChoices.ORGANIZADOR,
		)
		self.admin = Usuario.objects.create_user(
			username="admin",
			password="SenhaSegura!2",
			nome="Admin Geral",
			telefone="61988887777",
			perfil=PerfilChoices.ADMIN,
		)
		self.aluno = Usuario.objects.create_user(
			username="aluno",
			password="SenhaSegura!3",
			nome="Aluno Teste",
			telefone="61977776666",
			perfil=PerfilChoices.ALUNO,
			instituicao="UnB",
		)
		self.professor = Usuario.objects.create_user(
			username="professor",
			password="SenhaSegura!4",
			nome="Professor Teste",
			telefone="61966665555",
			perfil=PerfilChoices.PROFESSOR,
			instituicao="IFB",
		)

		self.evento = Evento.objects.create(
			tipo=TipoEventoChoices.PALESTRA,
			data_inicio="2025-10-10",
			data_fim="2025-10-11",
			local="Auditório Central",
			capacidade=1,
			organizador=self.organizador,
		)

	def test_usuario_aluno_deve_ter_instituicao(self):
		usuario = Usuario(
			username="aluno_sem_ies",
			nome="Aluno Sem IES",
			telefone="61900000000",
			perfil=PerfilChoices.ALUNO,
		)

		with self.assertRaises(ValidationError):
			usuario.full_clean()

	def test_evento_vagas_disponiveis(self):
		self.assertEqual(self.evento.vagas_disponiveis, 1)

		Inscricao.objects.create(
			evento=self.evento,
			participante=self.aluno,
			status=InscricaoStatus.CONFIRMADA,
		)

		self.evento.refresh_from_db()
		self.assertEqual(self.evento.vagas_disponiveis, 0)

	def test_inscricao_capacidade_maxima(self):
		Inscricao.objects.create(
			evento=self.evento,
			participante=self.aluno,
			status=InscricaoStatus.CONFIRMADA,
		)

		with self.assertRaises(ValidationError):
			Inscricao.objects.create(
				evento=self.evento,
				participante=self.professor,
				status=InscricaoStatus.CONFIRMADA,
			)

	def test_certificado_requer_presenca_confirmada(self):
		inscricao = Inscricao.objects.create(
			evento=self.evento,
			participante=self.aluno,
			status=InscricaoStatus.CONFIRMADA,
		)

		with self.assertRaises(ValidationError):
			Certificado.objects.create(
				inscricao=inscricao,
				emitido_por=self.organizador,
				carga_horaria=4,
			)

		inscricao.presenca_confirmada = True
		inscricao.save()

		certificado = Certificado.objects.create(
			inscricao=inscricao,
			emitido_por=self.admin,
			carga_horaria=4,
		)

		self.assertTrue(certificado.codigo)
