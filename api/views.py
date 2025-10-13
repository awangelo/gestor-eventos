from __future__ import annotations

from datetime import date

from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.generic import TemplateView

from .models import (
	Certificado,
	Evento,
	Inscricao,
	InscricaoStatus,
	InstituicaoChoices,
	PerfilChoices,
	TipoEventoChoices,
	Usuario,
)


def _flatten_validation_errors(error: ValidationError) -> list[str]:
	if hasattr(error, "error_dict"):
		flat_errors: list[str] = []
		for field, messages in error.message_dict.items():
			for message in messages:
				flat_errors.append(f"{field}: {message}")
		return flat_errors
	if hasattr(error, "error_list"):
		return [str(e) for e in error.error_list]
	return [str(error)]


class PostFeedbackMixin:
	success_context_name = "form_success"
	error_context_name = "form_errors"
	data_context_name = "form_data"

	def render_post_response(self, *, errors: list[str] | None = None, success: str | None = None, clear_data: bool = False, **kwargs):
		context = self.get_context_data(**kwargs)
		context[self.data_context_name] = {} if clear_data else self.request.POST.dict()
		if errors:
			context[self.error_context_name] = errors
		if success:
			context[self.success_context_name] = success
		return self.render_to_response(context)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.setdefault(self.data_context_name, {})
		return context


class CadastroUsuarioView(PostFeedbackMixin, TemplateView):
	template_name = "api/cadastro_usuario.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["perfis"] = PerfilChoices.choices
		context["instituicoes"] = InstituicaoChoices.choices
		context["usuarios_existentes"] = (
			Usuario.objects.select_related()
			.order_by("nome", "username")
		)
		return context

	def post(self, request, *args, **kwargs):
		data = request.POST
		errors: list[str] = []

		nome = data.get("nome", "").strip()
		username = data.get("username", "").strip()
		email = data.get("email", "").strip()
		telefone = data.get("telefone", "").strip()
		perfil = data.get("perfil", "").strip()
		instituicao_raw = data.get("instituicao", "").strip()
		senha = data.get("senha", "").strip() or None

		if not nome:
			errors.append("Informe o nome completo.")
		if not username:
			errors.append("Informe o usuário de login.")
		if not email:
			errors.append("Informe o e-mail.")
		if not telefone:
			errors.append("Informe o telefone.")
		if not perfil:
			errors.append("Selecione um perfil válido.")
		elif perfil not in dict(PerfilChoices.choices):
			errors.append("Perfil informado é inválido.")

		instituicao = instituicao_raw or None
		if perfil in {PerfilChoices.ALUNO, PerfilChoices.PROFESSOR} and not instituicao:
			errors.append("Instituição é obrigatória para alunos e professores.")

		if errors:
			return self.render_post_response(errors=errors)

		try:
			usuario = Usuario.objects.create_user(
				username=username,
				password=senha,
				email=email,
				nome=nome,
				telefone=telefone,
				perfil=perfil,
				instituicao=instituicao,
			)
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Usuário ou e-mail já cadastrado.")

		if errors:
			return self.render_post_response(errors=errors)

		success = f"Usuário '{usuario.username}' criado com sucesso."
		return self.render_post_response(success=success, clear_data=True)


class CadastroEventoView(PostFeedbackMixin, TemplateView):
	template_name = "api/cadastro_evento.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["tipos_evento"] = TipoEventoChoices.choices
		context["organizadores"] = (
			Usuario.objects.filter(perfil__in=[
				PerfilChoices.ADMIN,
				PerfilChoices.ORGANIZADOR,
			])
			.order_by("nome", "username")
		)
		return context


	def post(self, request, *args, **kwargs):
		data = request.POST
		errors: list[str] = []

		tipo = data.get("tipo", "").strip()
		local = data.get("local", "").strip()
		data_inicio_raw = data.get("data_inicio")
		data_fim_raw = data.get("data_fim")
		capacidade_raw = data.get("capacidade")
		organizador_id = data.get("organizador")

		if not tipo:
			errors.append("Selecione o tipo de evento.")
		elif tipo not in dict(TipoEventoChoices.choices):
			errors.append("Tipo de evento inválido.")
		if not local:
			errors.append("Informe o local do evento.")

		try:
			data_inicio = date.fromisoformat(data_inicio_raw) if data_inicio_raw else None
		except ValueError:
			errors.append("Data de início inválida.")
			data_inicio = None

		try:
			data_fim = date.fromisoformat(data_fim_raw) if data_fim_raw else None
		except ValueError:
			errors.append("Data de término inválida.")
			data_fim = None

		try:
			capacidade = int(capacidade_raw) if capacidade_raw else None
			if capacidade is not None and capacidade <= 0:
				errors.append("Informe uma capacidade maior que zero.")
		except (TypeError, ValueError):
			capacidade = None
			errors.append("Capacidade inválida.")

		organizador = None
		if not organizador_id:
			errors.append("Selecione um organizador responsável.")
		else:
			try:
				organizador = Usuario.objects.get(
					pk=organizador_id,
					perfil__in=[PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR],
				)
			except Usuario.DoesNotExist:
				errors.append("Organizador informado não é válido.")

		if not data_inicio:
			errors.append("Informe a data de início.")
		if not data_fim:
			errors.append("Informe a data de término.")
		if capacidade is None:
			errors.append("Informe a capacidade do evento.")

		if errors:
			return self.render_post_response(errors=errors)

		try:
			evento = Evento.objects.create(
				tipo=tipo,
				data_inicio=data_inicio,
				data_fim=data_fim,
				local=local,
				capacidade=capacidade,
				organizador=organizador,
			)
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Não foi possível cadastrar o evento. Tente novamente.")

		if errors:
			return self.render_post_response(errors=errors)

		success = f"Evento '{evento}' cadastrado com sucesso."
		return self.render_post_response(success=success, clear_data=True)


class InscricaoUsuarioView(PostFeedbackMixin, TemplateView):
	template_name = "api/inscricao_usuario.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["eventos"] = (
			Evento.objects.select_related("organizador")
			.order_by("data_inicio", "tipo")
		)
		context["participantes"] = (
			Usuario.objects.filter(perfil__in=[
				PerfilChoices.ALUNO,
				PerfilChoices.PROFESSOR,
			])
			.order_by("nome", "username")
		)
		context["status_inscricao"] = InscricaoStatus.choices
		return context


	def post(self, request, *args, **kwargs):
		data = request.POST
		errors: list[str] = []

		evento_id = data.get("evento")
		participante_id = data.get("participante")
		status = data.get("status", InscricaoStatus.PENDENTE)
		presenca_confirmada = data.get("presenca_confirmada") == "on"

		if not evento_id:
			errors.append("Escolha um evento.")
		if not participante_id:
			errors.append("Selecione um participante.")
		if status not in dict(InscricaoStatus.choices):
			errors.append("Status de inscrição inválido.")

		if errors:
			return self.render_post_response(errors=errors)

		try:
			inscricao, created = Inscricao.objects.get_or_create(
				evento_id=evento_id,
				participante_id=participante_id,
				defaults={"status": status, "presenca_confirmada": presenca_confirmada},
			)
			if not created:
				inscricao.status = status
				inscricao.presenca_confirmada = presenca_confirmada
				inscricao.save()
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Não foi possível registrar a inscrição.")

		if errors:
			return self.render_post_response(errors=errors)

		action = " criada" if created else " atualizada"
		success = f"Inscrição{action} com sucesso."
		return self.render_post_response(success=success, clear_data=True)


class EmissaoCertificadoView(PostFeedbackMixin, TemplateView):
	template_name = "api/emissao_certificado.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["inscricoes_elegiveis"] = (
			Inscricao.objects.filter(
				status=InscricaoStatus.CONFIRMADA,
				presenca_confirmada=True,
			)
			.select_related("evento", "participante")
			.order_by("-data_inscricao")
		)
		context["emissores"] = (
			Usuario.objects.filter(perfil__in=[
				PerfilChoices.ADMIN,
				PerfilChoices.ORGANIZADOR,
			])
			.order_by("nome", "username")
		)
		return context


	def post(self, request, *args, **kwargs):
		data = request.POST
		errors: list[str] = []

		inscricao_id = data.get("inscricao")
		emissor_id = data.get("emitido_por")
		carga_raw = data.get("carga_horaria") or data.get("carga") or data.get("cert_carga")
		validade_raw = data.get("validade")
		observacoes = data.get("observacoes", "").strip()

		if not inscricao_id:
			errors.append("Selecione uma inscrição elegível.")
		if not emissor_id:
			errors.append("Selecione o emissor.")

		carga_horaria = None
		if not carga_raw:
			errors.append("Informe a carga horária.")
		else:
			try:
				carga_horaria = int(carga_raw)
				if carga_horaria <= 0:
					errors.append("Informe uma carga horária positiva.")
			except (TypeError, ValueError):
				errors.append("Carga horária inválida.")

		validade = None
		if validade_raw:
			try:
				validade = date.fromisoformat(validade_raw)
			except ValueError:
				errors.append("Data de validade inválida.")

		if errors:
			return self.render_post_response(errors=errors)

		try:
			inscricao = Inscricao.objects.select_related("evento", "participante").get(pk=inscricao_id)
		except Inscricao.DoesNotExist:
			return self.render_post_response(errors=["Inscrição selecionada não foi encontrada."])

		if inscricao.status != InscricaoStatus.CONFIRMADA or not inscricao.presenca_confirmada:
			return self.render_post_response(errors=["A inscrição precisa estar confirmada com presença registrada."])

		try:
			emissor = Usuario.objects.get(
				pk=emissor_id,
				perfil__in=[PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR],
			)
		except Usuario.DoesNotExist:
			return self.render_post_response(errors=["Emissor selecionado não é válido."])

		try:
			certificado, created = Certificado.objects.update_or_create(
				inscricao=inscricao,
				defaults={
					"emitido_por": emissor,
					"carga_horaria": carga_horaria,
					"validade": validade,
					"observacoes": observacoes,
				},
			)
		except ValidationError as exc:
			return self.render_post_response(errors=_flatten_validation_errors(exc))

		success = (
			"Certificado emitido com sucesso." if created else "Certificado atualizado com sucesso."
		)
		return self.render_post_response(success=success, clear_data=True)


class AutenticacaoView(PostFeedbackMixin, TemplateView):
	template_name = "api/autenticacao.html"

	def post(self, request, *args, **kwargs):
		data = request.POST
		errors: list[str] = []

		username = data.get("username", "").strip()
		password = data.get("password", "")

		if not username or not password:
			errors.append("Informe usuário/e-mail e senha.")
			return self.render_post_response(errors=errors)

		user = authenticate(request, username=username, password=password)
		if user is None:
			return self.render_post_response(errors=["Credenciais inválidas."])

		login(request, user)
		if data.get("remember_me") == "on":
			request.session.set_expiry(None)
		else:
			request.session.set_expiry(0)
		success = f"Autenticado como {user.get_username()}."
		return self.render_post_response(success=success, clear_data=True)
