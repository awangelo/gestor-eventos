from django.db import models
from django.db.models import Q, F
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class InstituicaoChoices(models.TextChoices):
    UNB = "UNB", "UnB"
    IFB = "IFB", "IFB"
    CEUB = "CEUB", "CEUB"
    IESB = "IESB", "IESB"
    UCB = "UCB", "UCB"
    OUTRA = "OUTRA", "Outra"


class PerfilChoices(models.TextChoices):
    ALUNO = "ALUNO", "Aluno"
    PROFESSOR = "PROFESSOR", "Professor"
    ORGANIZADOR = "ORGANIZADOR", "Organizador"
    ADMIN = "ADMIN", "Admin"
    VISITANTE = "VISITANTE", "Visitante"


class Usuario(AbstractUser):
    # username, password, first_name, last_name, email etc já existem
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    instituicao = models.CharField(
        max_length=20,
        choices=InstituicaoChoices.choices,
        blank=True,
        null=True,
        help_text="Obrigatório para perfis ALUNO e PROFESSOR."
    )
    perfil = models.CharField(
        max_length=20,
        choices=PerfilChoices.choices
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="instituicao_required_for_aluno_prof",
                check=(
                    ~Q(perfil__in=[PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]) |
                    (Q(instituicao__isnull=False) & ~Q(instituicao=""))
                )
            )
        ]
        indexes = [
            models.Index(fields=["perfil"]),
        ]

    def clean(self):
        super().clean()
        if self.perfil in {PerfilChoices.ALUNO, PerfilChoices.PROFESSOR} and not self.instituicao:
            raise ValidationError({"instituicao": "Instituição é obrigatória para este perfil."})

    def __str__(self):
        return f"{self.username} ({self.perfil})"


class TipoEventoChoices(models.TextChoices):
    PALESTRA = "PALESTRA", "Palestra"
    WORKSHOP = "WORKSHOP", "Workshop"
    MINICURSO = "MINICURSO", "Minicurso"
    SEMINARIO = "SEMINARIO", "Seminário"
    OUTRO = "OUTRO", "Outro"


class Evento(models.Model):
    tipo = models.CharField(max_length=20, choices=TipoEventoChoices.choices)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    local = models.CharField(max_length=150)
    capacidade = models.PositiveIntegerField()
    organizador = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
        limit_choices_to=Q(perfil__in=[PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR])
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["data_inicio", "tipo"]
        indexes = [
            models.Index(fields=["data_inicio"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["organizador"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="evento_data_fim_gte_inicio",
                check=Q(data_fim__gte=F("data_inicio"))
            ),
            models.CheckConstraint(
                name="capacidade_positive",
                check=Q(capacidade__gt=0)
            ),
        ]

    def clean(self):
        super().clean()
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "Data fim não pode ser anterior à data início."})
        if self.organizador and self.organizador.perfil not in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
            raise ValidationError({"organizador": "Usuário deve ter perfil ADMIN ou ORGANIZADOR."})

    def __str__(self):
        return f"{self.tipo} - {self.local} ({self.data_inicio})"