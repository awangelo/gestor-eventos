from __future__ import annotations

import json
import os
import re
from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from fpdf import FPDF

from .decorators import perfil_required, admin_required, organizador_or_admin_required, aluno_professor_required

from .models import (
	Certificado,
	Evento,
	Inscricao,
	InscricaoStatus,
	InstituicaoChoices,
	PerfilChoices,
	TipoEventoChoices,
	Usuario,
	AuditLog,
)
from .audit import (
	log_usuario_criado,
	log_evento_criado,
	log_evento_atualizado,
	log_evento_excluido,
	log_inscricao_criada,
	log_inscricao_atualizada,
	log_inscricao_cancelada,
	log_certificado_gerado,
	log_certificado_consultado,
	log_login,
	log_logout,
)
from .emails import (
	enviar_email_boas_vindas,
	enviar_email_certificado,
)


def _validate_image_file(file) -> str | None:
	"""
	Validate that the uploaded file is an image.
	Returns error message if invalid, None if valid. 
	"""
	if not file:
		return None
	
	# Check file extension
	allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
	file_ext = os.path.splitext(file.name)[1].lower()
	
	if file_ext not in allowed_extensions:
		return f"Formato de arquivo inválido. Use: {', '.join(allowed_extensions)}"
	
	# Check MIME type
	allowed_mime_types = [
		'image/jpeg',
		'image/png',
		'image/gif',
		'image/bmp',
		'image/webp',
		'image/svg+xml'
	]
	
	if hasattr(file, 'content_type') and file.content_type not in allowed_mime_types:
		return "O arquivo enviado não é uma imagem válida."
	
	# Check file size (max 5MB)
	max_size = 5 * 1024 * 1024  # 5MB in bytes
	if file.size > max_size:
		return "A imagem deve ter no máximo 5MB."
	
	return None


def _validate_password(password: str) -> str | None:
	"""
	Validate password meets security criteria:
	- At least 8 characters
	- Contains letters
	- Contains numbers
	- Contains special characters
	Returns error message if invalid, None if valid.
	"""
	if not password:
		return "A senha é obrigatória."
	
	if len(password) < 8:
		return "A senha deve ter no mínimo 8 caracteres."
	
	if not re.search(r'[a-zA-Z]', password):
		return "A senha deve conter pelo menos uma letra."
	
	if not re.search(r'\d', password):
		return "A senha deve conter pelo menos um número."
	
	if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]', password):
		return "A senha deve conter pelo menos um caractere especial."
	
	return None


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


@method_decorator(admin_required, name='dispatch')
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
		senha = data.get("senha", "").strip()
		confirmar_senha = data.get("confirmar_senha", "").strip()

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

		# Validate password
		password_error = _validate_password(senha)
		if password_error:
			errors.append(password_error)
		elif senha != confirmar_senha:
			errors.append("As senhas não coincidem.")

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
			
			# Log user creation
			criado_por = request.user if request.user.is_authenticated else None
			log_usuario_criado(request, usuario, criado_por)
			
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Usuário ou e-mail já cadastrado.")

		if errors:
			return self.render_post_response(errors=errors)

		success = f"Usuário '{usuario.username}' criado com sucesso."
		return self.render_post_response(success=success, clear_data=True)


@method_decorator(organizador_or_admin_required, name='dispatch')
class CadastroEventoView(PostFeedbackMixin, TemplateView):
	template_name = "api/cadastro_evento.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["tipos_evento"] = TipoEventoChoices.choices
		context["is_admin"] = self.request.user.perfil == PerfilChoices.ADMIN
		context["organizadores"] = (
			Usuario.objects.filter(perfil__in=[
				PerfilChoices.ADMIN,
				PerfilChoices.ORGANIZADOR,
			])
			.order_by("nome", "username")
		)
		context["professores"] = (
			Usuario.objects.filter(perfil=PerfilChoices.PROFESSOR)
			.order_by("nome", "username")
		)
		return context


	def post(self, request, *args, **kwargs):
		data = request.POST
		files = request.FILES
		errors: list[str] = []

		tipo = data.get("tipo", "").strip()
		titulo = data.get("titulo", "").strip()
		local = data.get("local", "").strip()
		data_inicio_raw = data.get("data_inicio")
		data_fim_raw = data.get("data_fim")
		horario_raw = data.get("horario")
		capacidade_raw = data.get("capacidade")
		organizador_id = data.get("organizador")
		professor_id = data.get("professor_responsavel")
		banner = files.get("banner")

		if not tipo:
			errors.append("Selecione o tipo de evento.")
		elif tipo not in dict(TipoEventoChoices.choices):
			errors.append("Tipo de evento inválido.")
		if not local:
			errors.append("Informe o local do evento.")

		# Validate banner image if provided
		if banner:
			banner_error = _validate_image_file(banner)
			if banner_error:
				errors.append(banner_error)

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
		# If user is admin, they can select any organizer; otherwise, use the current user
		if request.user.perfil == PerfilChoices.ADMIN:
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
		else:
			# Non-admin users (organizers) are automatically set as the organizer
			organizador = request.user

		professor = None
		if not professor_id:
			errors.append("Selecione um professor responsável.")
		else:
			try:
				professor = Usuario.objects.get(
					pk=professor_id,
					perfil=PerfilChoices.PROFESSOR,
				)
			except Usuario.DoesNotExist:
				errors.append("Professor informado não é válido.")

		if not data_inicio:
			errors.append("Informe a data de início.")
		elif data_inicio < date.today():
			errors.append("A data de início não pode ser anterior à data atual.")
		if not data_fim:
			errors.append("Informe a data de término.")
		if capacidade is None:
			errors.append("Informe a capacidade do evento.")

		if errors:
			return self.render_post_response(errors=errors)

		try:
			evento = Evento.objects.create(
				tipo=tipo,
				titulo=titulo,
				data_inicio=data_inicio,
				data_fim=data_fim,
				horario=horario_raw or None,
				local=local,
				capacidade=capacidade,
				organizador=organizador,
				professor_responsavel=professor,
				banner=banner,
			)
			
			# Log event creation
			log_evento_criado(request, evento)
			
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Não foi possível cadastrar o evento. Tente novamente.")
		except Exception as e:
			# Catch potential image validation errors from Pillow if not caught by ValidationError
			errors.append(f"Erro ao salvar evento: {str(e)}")

		if errors:
			return self.render_post_response(errors=errors)

		success = f"Evento '{evento}' cadastrado com sucesso."
		return self.render_post_response(success=success, clear_data=True)


@method_decorator(perfil_required(PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR, PerfilChoices.PROFESSOR), name='dispatch')
class EditarEventoView(PostFeedbackMixin, TemplateView):
	template_name = "api/editar_evento.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		evento_id = self.kwargs.get('evento_id')
		evento = get_object_or_404(Evento, pk=evento_id)
		
		# Check permission: Admin can edit any, Organizador only their own, Professor only if responsible
		if self.request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != self.request.user:
			from django.core.exceptions import PermissionDenied
			raise PermissionDenied("Você não tem permissão para editar este evento.")
		
		if self.request.user.perfil == PerfilChoices.PROFESSOR and evento.professor_responsavel != self.request.user:
			from django.core.exceptions import PermissionDenied
			raise PermissionDenied("Você não tem permissão para editar este evento.")
		
		context["evento"] = evento
		context["tipos_evento"] = TipoEventoChoices.choices
		context["organizadores"] = (
			Usuario.objects.filter(perfil__in=[
				PerfilChoices.ADMIN,
				PerfilChoices.ORGANIZADOR,
			])
			.order_by("nome", "username")
		)
		context["professores"] = (
			Usuario.objects.filter(perfil=PerfilChoices.PROFESSOR)
			.order_by("nome", "username")
		)
		return context

	def post(self, request, *args, **kwargs):
		evento_id = self.kwargs.get('evento_id')
		evento = get_object_or_404(Evento, pk=evento_id)
		
		# Check permission
		if request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != request.user:
			return self.render_post_response(errors=["Você não tem permissão para editar este evento."])
		
		if request.user.perfil == PerfilChoices.PROFESSOR and evento.professor_responsavel != request.user:
			return self.render_post_response(errors=["Você não tem permissão para editar este evento."])
		
		data = request.POST
		files = request.FILES
		errors: list[str] = []

		tipo = data.get("tipo", "").strip()
		titulo = data.get("titulo", "").strip()
		local = data.get("local", "").strip()
		data_inicio_raw = data.get("data_inicio")
		data_fim_raw = data.get("data_fim")
		horario_raw = data.get("horario")
		capacidade_raw = data.get("capacidade")
		organizador_id = data.get("organizador")
		professor_id = data.get("professor_responsavel")
		banner = files.get("banner")
		remover_banner = data.get("remover_banner") == "on"

		if not tipo:
			errors.append("Selecione o tipo de evento.")
		elif tipo not in dict(TipoEventoChoices.choices):
			errors.append("Tipo de evento inválido.")
		if not local:
			errors.append("Informe o local do evento.")

		# Validate banner image if provided
		if banner:
			banner_error = _validate_image_file(banner)
			if banner_error:
				errors.append(banner_error)

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

		professor = None
		if not professor_id:
			errors.append("Selecione um professor responsável.")
		else:
			try:
				professor = Usuario.objects.get(
					pk=professor_id,
					perfil=PerfilChoices.PROFESSOR,
				)
			except Usuario.DoesNotExist:
				errors.append("Professor informado não é válido.")

		if not data_inicio:
			errors.append("Informe a data de início.")
		if not data_fim:
			errors.append("Informe a data de término.")
		if capacidade is None:
			errors.append("Informe a capacidade do evento.")

		if errors:
			return self.render_post_response(errors=errors)

		try:
			# Track changed fields
			campos_alterados = []
			if evento.tipo != tipo:
				campos_alterados.append('tipo')
			if evento.titulo != titulo:
				campos_alterados.append('titulo')
			if evento.local != local:
				campos_alterados.append('local')
			if evento.data_inicio != data_inicio:
				campos_alterados.append('data_inicio')
			if evento.data_fim != data_fim:
				campos_alterados.append('data_fim')
			if evento.horario != (horario_raw or None):
				campos_alterados.append('horario')
			if evento.capacidade != capacidade:
				campos_alterados.append('capacidade')
			if evento.organizador_id != int(organizador_id):
				campos_alterados.append('organizador')
			if evento.professor_responsavel_id != int(professor_id):
				campos_alterados.append('professor_responsavel')
			
			# Update fields
			evento.tipo = tipo
			evento.titulo = titulo
			evento.local = local
			evento.data_inicio = data_inicio
			evento.data_fim = data_fim
			evento.horario = horario_raw or None
			evento.capacidade = capacidade
			evento.organizador = organizador
			evento.professor_responsavel = professor
			
			if banner:
				evento.banner = banner
				campos_alterados.append('banner')
			elif remover_banner and evento.banner:
				evento.banner.delete()
				evento.banner = None
				campos_alterados.append('banner')
			
			evento.save()
			
			# Log event update
			log_evento_atualizado(request, evento, campos_alterados)
			
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Não foi possível atualizar o evento. Tente novamente.")
		except Exception as e:
			errors.append(f"Erro ao salvar evento: {str(e)}")

		if errors:
			return self.render_post_response(errors=errors)

		messages.success(request, f"Evento '{evento}' atualizado com sucesso.")
		return redirect('detalhes-evento', evento_id=evento.pk)


@method_decorator(organizador_or_admin_required, name='dispatch')
class DeletarEventoView(TemplateView):
	template_name = "api/deletar_evento.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		evento_id = self.kwargs.get('evento_id')
		evento = get_object_or_404(Evento, pk=evento_id)
		
		# Check permission: Admin can delete any, Organizador only their own
		if self.request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != self.request.user:
			from django.core.exceptions import PermissionDenied
			raise PermissionDenied("Você não tem permissão para deletar este evento.")
		
		context["evento"] = evento
		return context

	def post(self, request, *args, **kwargs):
		evento_id = self.kwargs.get('evento_id')
		evento = get_object_or_404(Evento, pk=evento_id)
		
		# Check permission
		if request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != request.user:
			messages.error(request, "Você não tem permissão para deletar este evento.")
			return redirect('dashboard')
		
		# Capture event info before deletion
		evento_info = {
			'id': evento.id,
			'tipo': evento.tipo,
			'titulo': evento.titulo,
			'local': evento.local,
			'data_inicio': evento.data_inicio.isoformat(),
			'data_fim': evento.data_fim.isoformat() if evento.data_fim else None,
		}
		evento_nome = str(evento)
		
		# Delete the event
		evento.delete()
		
		# Log deletion
		log_evento_excluido(request, evento_info)
		
		messages.success(request, f"Evento '{evento_nome}' deletado com sucesso.")
		return redirect('dashboard')


@method_decorator(login_required(login_url='login'), name='dispatch')
class InscricaoUsuarioView(PostFeedbackMixin, TemplateView):
	template_name = "api/inscricao_usuario.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Filter events based on user role
		if self.request.user.perfil == PerfilChoices.ORGANIZADOR:
			# ORGANIZADOR only sees their own events
			context["eventos"] = (
				Evento.objects.filter(organizador=self.request.user)
				.select_related("organizador")
				.order_by("data_inicio", "tipo")
			)
		else:
			# ADMIN, ALUNO, PROFESSOR see all events
			context["eventos"] = (
				Evento.objects.select_related("organizador")
				.order_by("data_inicio", "tipo")
			)
		
		# Only ADMIN and ORGANIZADOR can see participant dropdown
		if self.request.user.perfil in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
			# Get all inscribed participants grouped by event with their status
			inscricoes = Inscricao.objects.select_related('evento', 'participante').all()
			
			# Create mappings:
			# 1. event_id -> list of participant_ids
			# 2. "event_id_participant_id" -> status
			evento_participantes = {}
			inscricao_status_map = {}
			
			for inscricao in inscricoes:
				evento_id = inscricao.evento_id
				participante_id = inscricao.participante_id
				
				if evento_id not in evento_participantes:
					evento_participantes[evento_id] = []
				evento_participantes[evento_id].append(participante_id)
				
				# Store status with composite key
				key = f"{evento_id}_{participante_id}"
				inscricao_status_map[key] = inscricao.get_status_display()
			
			context["evento_participantes_json"] = json.dumps(evento_participantes)
			context["inscricao_status_map_json"] = json.dumps(inscricao_status_map)
			context["participantes"] = (
				Usuario.objects.filter(perfil__in=[
					PerfilChoices.ALUNO,
					PerfilChoices.PROFESSOR,
				])
				.order_by("nome", "username")
			)
			context["status_inscricao"] = InscricaoStatus.choices
		else:
			# Students and professors only register themselves
			context["participantes"] = None
			context["status_inscricao"] = None
		
		return context


	def post(self, request, *args, **kwargs):
		data = request.POST
		errors: list[str] = []

		evento_id = data.get("evento")
		
		# Determine participant based on role
		if request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
			# Students/Professors can only register themselves
			participante_id = request.user.pk
			status = InscricaoStatus.PENDENTE
			presenca_confirmada = False
		elif request.user.perfil == PerfilChoices.ORGANIZADOR:
			# ORGANIZADOR cannot register themselves, only others
			participante_id = data.get("participante")
			status = data.get("status", InscricaoStatus.PENDENTE)
			presenca_confirmada = False
			
			if not participante_id:
				errors.append("Selecione um participante.")
			# Prevent organizador from selecting themselves
			elif str(participante_id) == str(request.user.pk):
				errors.append("Organizadores não podem se inscrever em eventos.")
			if status not in dict(InscricaoStatus.choices):
				errors.append("Status de inscrição inválido.")
		else:
			# ADMIN can register others
			participante_id = data.get("participante")
			status = data.get("status", InscricaoStatus.PENDENTE)
			presenca_confirmada = False
			
			if not participante_id:
				errors.append("Selecione um participante.")
			if status not in dict(InscricaoStatus.choices):
				errors.append("Status de inscrição inválido.")

		if not evento_id:
			errors.append("Escolha um evento.")

		if errors:
			return self.render_post_response(errors=errors)

		# Additional validation: check that participante is Aluno or Professor
		if participante_id:
			try:
				participante = Usuario.objects.get(pk=participante_id)
				if participante.perfil not in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
					return self.render_post_response(errors=["Apenas alunos e professores podem ser inscritos em eventos."])
				if participante.perfil == PerfilChoices.ORGANIZADOR:
					return self.render_post_response(errors=["Organizadores não podem se inscrever em eventos."])
			except Usuario.DoesNotExist:
				return self.render_post_response(errors=["Participante não encontrado."])

		# Validate ORGANIZADOR can only manage their own events
		if request.user.perfil == PerfilChoices.ORGANIZADOR:
			try:
				evento = Evento.objects.get(pk=evento_id, organizador=request.user)
			except Evento.DoesNotExist:
				return self.render_post_response(errors=["Você não tem permissão para gerenciar inscrições deste evento."])
		else:
			# ADMIN can manage any event, ALUNO/PROFESSOR already validated
			try:
				evento = Evento.objects.get(pk=evento_id)
			except Evento.DoesNotExist:
				return self.render_post_response(errors=["Evento não encontrado."])

		# Check if user is already registered in this event
		existing_inscricao = Inscricao.objects.filter(
			evento_id=evento_id,
			participante_id=participante_id
		).first()
		
		if existing_inscricao:
			# If already registered, only allow status update
			if request.user.perfil in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
				# ADMIN/ORGANIZADOR can update status
				# Warning if trying to change status when presence is confirmed
				if existing_inscricao.presenca_confirmada and existing_inscricao.status != status:
					messages.warning(request, f"A presença deste participante já foi confirmada. O status foi alterado de {existing_inscricao.get_status_display()} para {dict(InscricaoStatus.choices)[status]}. A presença foi removida pois o novo status não é 'Confirmada'.")
					# Reset presence if status is not CONFIRMADA
					if status != InscricaoStatus.CONFIRMADA:
						existing_inscricao.presenca_confirmada = False
				existing_inscricao.status = status
				existing_inscricao.save()
				return self.render_post_response(success="Inscrição atualizada com sucesso.", clear_data=True)
			else:
				# ALUNO/PROFESSOR cannot register twice
				return self.render_post_response(errors=["Você já está inscrito neste evento."])
		
		# Check if event has available slots (only for new confirmations)
		if status == InscricaoStatus.CONFIRMADA:
			if evento.vagas_disponiveis <= 0:
				return self.render_post_response(errors=["O evento não possui vagas disponíveis."])
		
		# Check capacity for students (PENDENTE) as well if the event is full
		if request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
			if evento.vagas_disponiveis <= 0:
				return self.render_post_response(errors=["O evento não possui vagas disponíveis."])

		try:
			inscricao = Inscricao.objects.create(
				evento_id=evento_id,
				participante_id=participante_id,
				status=status,
			)
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Não foi possível registrar a inscrição.")

		if errors:
			return self.render_post_response(errors=errors)

		success = "Inscrição criada com sucesso."
		return self.render_post_response(success=success, clear_data=True)


@method_decorator(login_required(login_url='login'), name='dispatch')
class EmissaoCertificadoView(PostFeedbackMixin, TemplateView):
	template_name = "api/emissao_certificado.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		if self.request.user.perfil in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
			# Organizers and admins can issue certificates
			# ORGANIZADOR only sees inscricoes from their events
			inscricoes_query = Inscricao.objects.filter(
				status=InscricaoStatus.CONFIRMADA,
				presenca_confirmada=True,
			)
			if self.request.user.perfil == PerfilChoices.ORGANIZADOR:
				inscricoes_query = inscricoes_query.filter(evento__organizador=self.request.user)
			
			context["inscricoes_elegiveis"] = (
				inscricoes_query
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
			context["user_role"] = "issuer"
		else:
			# Students and professors can view their own certificates
			context["meus_certificados"] = (
				Certificado.objects.filter(inscricao__participante=self.request.user)
				.select_related("inscricao__evento", "emitido_por")
				.order_by("-emitido_em")
			)
			context["user_role"] = "recipient"
		
		return context


	def post(self, request, *args, **kwargs):
		# Only ADMIN and ORGANIZADOR can issue certificates
		if request.user.perfil not in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
			messages.error(request, "Você não tem permissão para emitir certificados.")
			return redirect('emissao-certificado')
		
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

		# Validate that validade is after the event end date
		if validade and inscricao.evento.data_fim and validade <= inscricao.evento.data_fim:
			return self.render_post_response(errors=["A data de validade deve ser posterior à data de término do evento."])

		# Validate ORGANIZADOR can only issue certificates for their own events
		if request.user.perfil == PerfilChoices.ORGANIZADOR:
			if inscricao.evento.organizador != request.user:
				return self.render_post_response(errors=["Você não tem permissão para emitir certificado para este evento."])

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
			
			# Log certificate generation
			log_certificado_gerado(request, certificado)
			
			# Send certificate email
			try:
				enviar_email_certificado(certificado)
			except Exception as e:
				# Se falhar o envio do email, não deve impedir a criação do certificado,
				# mas deve avisar o usuário.
				messages.warning(request, f"Certificado gerado, mas houve erro ao enviar o e-mail: {e}")
			
		except ValidationError as exc:
			return self.render_post_response(errors=_flatten_validation_errors(exc))

		success = (
			"Certificado emitido com sucesso." if created else "Certificado atualizado com sucesso."
		)
		return self.render_post_response(success=success, clear_data=True)


@method_decorator(login_required, name='dispatch')
class GerarCertificadoPDFView(View):
	def get(self, request, pk):
		certificado = get_object_or_404(Certificado, pk=pk)
		
		# Check permissions
		if request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
			if certificado.inscricao.participante != request.user:
				messages.error(request, "Você não tem permissão para visualizar este certificado.")
				return redirect('dashboard')
		elif request.user.perfil == PerfilChoices.ORGANIZADOR:
			if certificado.inscricao.evento.organizador != request.user:
				messages.error(request, "Você não tem permissão para visualizar este certificado.")
				return redirect('dashboard')
		# Admin can view all
		
		# Generate PDF
		pdf = FPDF(orientation='L', unit='mm', format='A4')
		pdf.add_page()
		
		# Border
		pdf.set_line_width(1)
		pdf.rect(10, 10, 277, 190)
		pdf.set_line_width(0.5)
		pdf.rect(12, 12, 273, 186)
		
		# Header
		pdf.set_font("Helvetica", "B", 30)
		pdf.set_text_color(50, 50, 50)
		pdf.cell(0, 40, "CERTIFICADO DE PARTICIPACAO", align="C", new_x="LMARGIN", new_y="NEXT")
		
		pdf.ln(10)
		
		# Body
		pdf.set_font("Helvetica", "", 16)
		pdf.set_text_color(0, 0, 0)
		
		# Remove accents for FPDF standard fonts or use a unicode font
		# For simplicity, I'll strip accents or use basic ASCII for now to avoid encoding issues with standard fonts
		# In a real app, we would load a TTF font.
		
		participante_nome = certificado.inscricao.participante.nome
		evento_titulo = certificado.inscricao.evento.titulo or certificado.inscricao.evento.get_tipo_display()
		evento_local = certificado.inscricao.evento.local
		
		# Simple accent replacement for standard fonts (Latin-1)
		def clean_text(text):
			return text.encode('latin-1', 'replace').decode('latin-1')

		try:
			texto = (
				f"Certificamos que {participante_nome} participou do evento "
				f"\"{evento_titulo}\", "
				f"realizado em {evento_local}, "
				f"com carga horaria de {certificado.carga_horaria} horas."
			)
			# FPDF default fonts support Latin-1
			texto = texto.encode('latin-1', 'replace').decode('latin-1')
		except:
			texto = "Erro na codificacao do texto."

		pdf.multi_cell(0, 10, texto, align="C", new_x="LMARGIN", new_y="NEXT")
		
		pdf.ln(20)
		
		# Date
		pdf.set_font("Helvetica", "", 14)
		data_str = f"Brasilia, {certificado.emitido_em.strftime('%d/%m/%Y')}"
		pdf.cell(0, 10, data_str, align="C", new_x="LMARGIN", new_y="NEXT")
		
		pdf.ln(30)
		
		# Signatures
		pdf.set_line_width(0.5)
		
		# Calculate positions for signatures
		y_pos = pdf.get_y()
		
		# Organizer Signature
		pdf.line(40, y_pos, 120, y_pos)
		pdf.set_xy(40, y_pos + 2)
		pdf.set_font("Helvetica", "B", 12)
		pdf.cell(80, 5, "Organizacao", align="C", new_x="LMARGIN", new_y="NEXT")
		
		# System Signature
		pdf.line(177, y_pos, 257, y_pos)
		pdf.set_xy(177, y_pos + 2)
		pdf.cell(80, 5, "AEGS - Gestao de Eventos", align="C", new_x="LMARGIN", new_y="NEXT")
		
		# Footer
		pdf.set_y(-20)
		pdf.set_font("Helvetica", "I", 8)
		pdf.set_text_color(128, 128, 128)
		pdf.cell(0, 10, f"Certificado gerado eletronicamente em {date.today().strftime('%d/%m/%Y')}", align="C")
		
		# Output
		response = HttpResponse(bytes(pdf.output()), content_type='application/pdf')
		response['Content-Disposition'] = f'attachment; filename="certificado_{certificado.id}.pdf"'
		
		# Log access
		log_certificado_consultado(request, certificado)
		
		return response


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
		
		# Log successful login
		log_login(request, user)
		
		if data.get("remember_me") == "on":
			request.session.set_expiry(None)
		else:
			request.session.set_expiry(0)
		
		messages.success(request, f"Bem-vindo, {user.nome if hasattr(user, 'nome') else user.get_username()}!")
		return redirect('dashboard')


@method_decorator(organizador_or_admin_required, name='dispatch')
class PresencaView(PostFeedbackMixin, TemplateView):
	template_name = "api/presenca.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Get all events (for organizador, filter by their events)
		if self.request.user.perfil == PerfilChoices.ORGANIZADOR:
			context["eventos"] = Evento.objects.filter(
				organizador=self.request.user
			).order_by("-data_inicio")
		else:
			context["eventos"] = Evento.objects.all().order_by("-data_inicio")
		
		# Get selected event if any
		evento_id = self.request.GET.get("evento")
		if evento_id:
			try:
				evento = Evento.objects.get(pk=evento_id)
				# Verify organizer has access to this event
				if self.request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != self.request.user:
					messages.error(self.request, "Você não tem permissão para gerenciar este evento.")
				else:
					context["evento_selecionado"] = evento
					context["inscricoes"] = Inscricao.objects.filter(
						evento=evento,
						status=InscricaoStatus.CONFIRMADA
					).select_related("participante").order_by("participante__nome")
			except Evento.DoesNotExist:
				pass
		
		return context

	def post(self, request, *args, **kwargs):
		errors = []
		evento_id = request.POST.get("evento")
		
		if not evento_id:
			return self.render_post_response(errors=["Selecione um evento."])
		
		try:
			evento = Evento.objects.get(pk=evento_id)
			# Verify organizer has access
			if request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != request.user:
				messages.error(request, "Você não tem permissão para gerenciar este evento.")
				return redirect('presenca')
		except Evento.DoesNotExist:
			return self.render_post_response(errors=["Evento não encontrado."])
		
		# Get all confirmed inscriptions for this event
		inscricoes = Inscricao.objects.filter(
			evento=evento,
			status=InscricaoStatus.CONFIRMADA
		)
		
		# Update presence for each inscription
		updated_count = 0
		for inscricao in inscricoes:
			presenca_marcada = f"presenca_{inscricao.pk}" in request.POST
			if inscricao.presenca_confirmada != presenca_marcada:
				inscricao.presenca_confirmada = presenca_marcada
				inscricao.save()
				updated_count += 1
		
		success = f"Presenças atualizadas com sucesso! ({updated_count} alterações)"
		return self.render_post_response(success=success)


@method_decorator(login_required(login_url='login'), name='dispatch')
class DashboardView(TemplateView):
	template_name = "api/dashboard.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# Add any additional context data if needed
		return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class DetalhesEventoView(PostFeedbackMixin, TemplateView):
	template_name = "api/detalhes_evento.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		evento_id = self.kwargs.get('evento_id')
		context['evento'] = get_object_or_404(
			Evento.objects.select_related('organizador', 'professor_responsavel'), 
			pk=evento_id
		)
		
		# Check if current user has an inscricao for this event
		if self.request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
			user_inscricao = Inscricao.objects.filter(
				evento_id=evento_id,
				participante=self.request.user
			).first()
			context['user_inscricao'] = user_inscricao
		
		# If user is ADMIN or Organizador of this event, provide inscricao management data
		if self.request.user.perfil in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
			# Check if user has permission to manage this event
			if self.request.user.perfil == PerfilChoices.ADMIN or context['evento'].organizador == self.request.user:
				# Get all inscricoes for this event
				inscricoes = Inscricao.objects.filter(
					evento_id=evento_id
				).select_related('participante').order_by('participante__nome')
				
				context['inscricoes'] = inscricoes
				
				# Get all potential participants
				all_participantes = Usuario.objects.filter(
					perfil__in=[PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]
				).order_by('nome')
				
				# Get list of already inscribed participant IDs
				inscribed_ids = set(inscricoes.values_list('participante_id', flat=True))
				
				# Filter to get only non-inscribed participants
				available_participantes = all_participantes.exclude(pk__in=inscribed_ids)
				
				context['participantes'] = all_participantes
				context['available_participantes'] = available_participantes
				context['status_inscricao'] = InscricaoStatus.choices
		
		return context
	
	def post(self, request, *args, **kwargs):
		"""Handle inscricao management for ADMIN/Organizador and cancellation for Aluno/Professor"""
		evento_id = self.kwargs.get('evento_id')
		evento = get_object_or_404(Evento, pk=evento_id)
		
		# Handle cancellation request from Aluno/Professor
		if 'cancel_inscricao' in request.POST:
			if request.user.perfil not in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
				return self.render_post_response(errors=["Você não tem permissão para cancelar inscrições."])
			
			try:
				inscricao = Inscricao.objects.get(
					evento_id=evento_id,
					participante=request.user
				)
				status_anterior = inscricao.status
				inscricao.status = InscricaoStatus.CANCELADA
				inscricao.save()
				
				# Log cancellation
				log_inscricao_cancelada(request, inscricao)
				
				return self.render_post_response(success="Sua inscrição foi cancelada com sucesso.", clear_data=True)
			except Inscricao.DoesNotExist:
				return self.render_post_response(errors=["Você não possui inscrição neste evento."])
		
		# Rest is for ADMIN/Organizador managing inscricoes
		# Check permission
		if request.user.perfil == PerfilChoices.ORGANIZADOR and evento.organizador != request.user:
			return self.render_post_response(errors=["Você não tem permissão para gerenciar este evento."])
		
		if request.user.perfil not in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
			return self.render_post_response(errors=["Você não tem permissão para gerenciar inscrições."])
		
		data = request.POST
		errors: list[str] = []
		
		participante_id = data.get("participante")
		status = data.get("status", InscricaoStatus.PENDENTE)
		
		if not participante_id:
			errors.append("Selecione um participante.")
		
		if status not in dict(InscricaoStatus.choices):
			errors.append("Status de inscrição inválido.")
		
		if errors:
			return self.render_post_response(errors=errors)
		
		# Validate that participante is Aluno or Professor
		try:
			participante = Usuario.objects.get(pk=participante_id)
			if participante.perfil not in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
				return self.render_post_response(errors=["Apenas alunos e professores podem ser inscritos em eventos."])
			if participante.perfil == PerfilChoices.ORGANIZADOR:
				return self.render_post_response(errors=["Organizadores não podem se inscrever em eventos."])
		except Usuario.DoesNotExist:
			return self.render_post_response(errors=["Participante não encontrado."])
		
		# Check if already registered
		existing_inscricao = Inscricao.objects.filter(
			evento_id=evento_id,
			participante_id=participante_id
		).first()
		
		if existing_inscricao:
			# Update existing inscricao
			status_anterior = existing_inscricao.status
			
			# Warning if trying to change status when presence is confirmed
			if existing_inscricao.presenca_confirmada and existing_inscricao.status != status:
				if status != InscricaoStatus.CONFIRMADA:
					messages.warning(request, f"A presença deste participante já foi confirmada. O status foi alterado de {existing_inscricao.get_status_display()} para {dict(InscricaoStatus.choices)[status]}. A presença foi removida pois o novo status não é 'Confirmada'.")
					existing_inscricao.presenca_confirmada = False

			existing_inscricao.status = status
			existing_inscricao.save()
			
			# Log update
			log_inscricao_atualizada(request, existing_inscricao, status_anterior)
			
			return self.render_post_response(success="Inscrição atualizada com sucesso.", clear_data=True)
		
		# Create new inscricao
		if status == InscricaoStatus.CONFIRMADA and evento.vagas_disponiveis <= 0:
			return self.render_post_response(errors=["O evento não possui vagas disponíveis."])
		
		try:
			inscricao = Inscricao.objects.create(
				evento_id=evento_id,
				participante_id=participante_id,
				status=status,
			)
			
			# Log creation
			log_inscricao_criada(request, inscricao)
			
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Não foi possível registrar a inscrição.")
		
		if errors:
			return self.render_post_response(errors=errors)
		
		success = "Inscrição criada com sucesso."
		return self.render_post_response(success=success, clear_data=True)


class SignupView(PostFeedbackMixin, TemplateView):
	"""Public signup view for ALUNO, PROFESSOR, and ORGANIZADOR"""
	template_name = "api/signup.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# Only allow certain profiles for self-registration
		context["perfis"] = [
			(PerfilChoices.ALUNO, "Aluno"),
			(PerfilChoices.PROFESSOR, "Professor"),
			(PerfilChoices.ORGANIZADOR, "Organizador"),
		]
		context["instituicoes"] = InstituicaoChoices.choices
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
		senha = data.get("senha", "").strip()
		confirmar_senha = data.get("confirmar_senha", "").strip()

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
		elif perfil not in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR, PerfilChoices.ORGANIZADOR]:
			errors.append("Perfil selecionado não é permitido para auto-cadastro.")

		# Validate password
		password_error = _validate_password(senha)
		if password_error:
			errors.append(password_error)
		elif senha != confirmar_senha:
			errors.append("As senhas não coincidem.")

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
			
			# Auto-login the user after successful registration
			login(request, usuario)
			
			# Send welcome email
			enviar_email_boas_vindas(usuario)
			
			messages.success(request, f"Conta criada com sucesso! Bem-vindo, {usuario.nome}!")
			return redirect('dashboard')
			
		except ValidationError as exc:
			errors.extend(_flatten_validation_errors(exc))
		except IntegrityError:
			errors.append("Usuário ou e-mail já cadastrado.")

		if errors:
			return self.render_post_response(errors=errors)

		return self.render_post_response(success="Conta criada com sucesso! Você será redirecionado...")


def logout_view(request):
	# Log before logout (while we still have the user)
	if request.user.is_authenticated:
		log_logout(request, request.user)
	
	logout(request)
	messages.success(request, "Você foi desconectado com sucesso.")
	return redirect('login')


@method_decorator(login_required(login_url='login'), name='dispatch')
class MeusEventosView(TemplateView):
    template_name = "api/meus_eventos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all inscriptions for the current user
        context["inscricoes"] = (
            Inscricao.objects.filter(participante=self.request.user)
            .select_related("evento", "certificado")
            .order_by("-evento__data_inicio")
        )
        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class PerfilUsuarioView(PostFeedbackMixin, TemplateView):
    template_name = "api/perfil_usuario.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["instituicoes"] = InstituicaoChoices.choices
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "delete":
            user = request.user
            # Log logout before deleting
            log_logout(request, user)
            logout(request)
            user.delete()
            messages.success(request, "Sua conta foi excluída com sucesso.")
            return redirect('login')
            
        # Update profile
        data = request.POST
        errors = []
        
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        telefone = data.get("telefone", "").strip()
        instituicao = data.get("instituicao", "").strip()
        
        if not nome:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("E-mail é obrigatório.")
            
        if request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR] and not instituicao:
            errors.append("Instituição é obrigatória.")
            
        if errors:
            return self.render_post_response(errors=errors)
            
        try:
            user = request.user
            user.nome = nome
            user.email = email
            user.telefone = telefone
            if instituicao:
                user.instituicao = instituicao
            user.save()
            
            messages.success(request, "Dados atualizados com sucesso.")
            return redirect('perfil-usuario')
            
        except IntegrityError:
            return self.render_post_response(errors=["E-mail já está em uso."])
        except Exception as e:
            return self.render_post_response(errors=[f"Erro ao atualizar dados: {str(e)}"])


@method_decorator(login_required, name='dispatch')
@method_decorator(organizador_or_admin_required, name='dispatch')
class AuditLogView(TemplateView):
    template_name = 'api/audit_logs.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        logs = AuditLog.objects.all().select_related('usuario', 'usuario_afetado', 'evento')
        
        # Filters
        data_filtro = self.request.GET.get('data')
        usuario_filtro = self.request.GET.get('usuario')
        
        if data_filtro:
            logs = logs.filter(data_hora__date=data_filtro)
            
        if usuario_filtro:
            logs = logs.filter(
                Q(usuario__username__icontains=usuario_filtro) | 
                Q(usuario__nome__icontains=usuario_filtro)
            )
            
        context['logs'] = logs
        context['data_filtro'] = data_filtro
        context['usuario_filtro'] = usuario_filtro
        return context
