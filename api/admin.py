from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Certificado, Evento, Inscricao, Usuario


class UsuarioCreationForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = Usuario
		fields = (
			"username",
			"nome",
			"email",
			"telefone",
			"perfil",
			"instituicao",
		)


class UsuarioChangeForm(UserChangeForm):
	class Meta(UserChangeForm.Meta):
		model = Usuario
		fields = (
			"username",
			"nome",
			"email",
			"telefone",
			"perfil",
			"instituicao",
			"is_active",
			"is_staff",
			"is_superuser",
			"groups",
			"user_permissions",
		)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
	add_form = UsuarioCreationForm
	form = UsuarioChangeForm
	list_display = (
		"username",
		"nome",
		"email",
		"telefone",
		"perfil",
		"instituicao",
		"is_active",
	)
	list_filter = ("perfil", "instituicao", "is_active", "is_staff")
	search_fields = ("username", "nome", "email", "telefone")

	fieldsets = UserAdmin.fieldsets + (
		(
			"Informações adicionais",
			{
				"fields": (
					"nome",
					"telefone",
					"instituicao",
					"perfil",
				)
			},
		),
	)

	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": (
					"username",
					"nome",
					"email",
					"telefone",
					"perfil",
					"instituicao",
					"password1",
					"password2",
				),
			},
		),
	)


class InscricaoInline(admin.TabularInline):
	model = Inscricao
	extra = 0
	readonly_fields = ("participante", "status", "data_inscricao")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
	list_display = (
		"tipo",
		"data_inicio",
		"data_fim",
		"local",
		"capacidade",
		"organizador",
		"vagas_disponiveis",
	)
	list_filter = ("tipo", "data_inicio", "organizador")
	search_fields = ("local", "organizador__nome")
	date_hierarchy = "data_inicio"
	inlines = [InscricaoInline]


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
	list_display = (
		"evento",
		"participante",
		"status",
		"presenca_confirmada",
		"data_inscricao",
	)
	list_filter = ("status", "evento__tipo")
	search_fields = ("evento__local", "participante__username", "participante__nome")
	autocomplete_fields = ("evento", "participante")


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
	list_display = (
		"codigo",
		"inscricao",
		"emitido_por",
		"carga_horaria",
		"emitido_em",
	)
	list_filter = ("emitido_em", "emitido_por")
	search_fields = ("codigo", "inscricao__participante__nome", "inscricao__evento__local")
	autocomplete_fields = ("inscricao", "emitido_por")
