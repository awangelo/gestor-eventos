import uuid

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


class InscricaoStatus(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    CANCELADA = "CANCELADA", "Cancelada"


class Evento(models.Model):
    tipo = models.CharField(max_length=20, choices=TipoEventoChoices.choices)
    titulo = models.CharField(max_length=150, blank=True, default="")
    data_inicio = models.DateField()
    data_fim = models.DateField()
    horario = models.TimeField(null=True, blank=True)
    local = models.CharField(max_length=150)
    capacidade = models.PositiveIntegerField()
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    organizador = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
        limit_choices_to=Q(perfil__in=[PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR])
    )
    professor_responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="eventos_responsavel",
        limit_choices_to=Q(perfil=PerfilChoices.PROFESSOR),
        help_text="Professor responsável pelo evento",
        null=True,
        blank=True,
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
        if self.professor_responsavel and self.professor_responsavel.perfil != PerfilChoices.PROFESSOR:
            raise ValidationError({"professor_responsavel": "O responsável deve ter perfil PROFESSOR."})

    def __str__(self):
        return f"{self.tipo} - {self.local} ({self.data_inicio})"

    @property
    def vagas_disponiveis(self) -> int:
        confirmadas = self.inscricoes.filter(status=InscricaoStatus.CONFIRMADA).count()
        return max(self.capacidade - confirmadas, 0)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Inscricao(models.Model):
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name="inscricoes",
    )
    participante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="inscricoes",
        limit_choices_to=Q(perfil__in=[PerfilChoices.ALUNO, PerfilChoices.PROFESSOR])
    )
    status = models.CharField(
        max_length=15,
        choices=InscricaoStatus.choices,
        default=InscricaoStatus.PENDENTE,
    )
    data_inscricao = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    presenca_confirmada = models.BooleanField(default=False)

    class Meta:
        unique_together = ("evento", "participante")
        indexes = [
            models.Index(fields=["evento", "status"]),
            models.Index(fields=["participante"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="inscricao_status_valido",
                check=Q(status__in=[choice[0] for choice in InscricaoStatus.choices])
            ),
        ]

    def clean(self):
        super().clean()
        if self.participante and self.participante.perfil not in [
            PerfilChoices.ALUNO,
            PerfilChoices.PROFESSOR,
        ]:
            raise ValidationError({
                "participante": "Inscrições só são permitidas para alunos ou professores. Organizadores não podem se inscrever em eventos."
            })
        
        # Extra validation: explicitly block ORGANIZADOR profile
        if self.participante and self.participante.perfil == PerfilChoices.ORGANIZADOR:
            raise ValidationError({
                "participante": "Organizadores não podem se inscrever em eventos."
            })

        if not self.evento_id:
            return

        if self.status == InscricaoStatus.CONFIRMADA:
            confirmadas = self.evento.inscricoes.filter(status=InscricaoStatus.CONFIRMADA)
            if self.pk:
                confirmadas = confirmadas.exclude(pk=self.pk)
            if confirmadas.count() >= self.evento.capacidade:
                raise ValidationError({
                    "evento": "Capacidade máxima atingida para este evento."
                })

        if self.presenca_confirmada and self.status != InscricaoStatus.CONFIRMADA:
            raise ValidationError({
                "presenca_confirmada": "A presença só pode ser confirmada para inscrições confirmadas."
            })

    def __str__(self):
        return f"{self.participante} -> {self.evento}"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Certificado(models.Model):
    inscricao = models.OneToOneField(
        Inscricao,
        on_delete=models.CASCADE,
        related_name="certificado"
    )
    emitido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="certificados_emitidos",
        limit_choices_to=Q(perfil__in=[PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR])
    )
    codigo = models.CharField(
        max_length=36,
        unique=True,
        editable=False,
        default=uuid.uuid4,
    )
    carga_horaria = models.PositiveIntegerField(help_text="Carga horária em horas.")
    emitido_em = models.DateTimeField(auto_now_add=True)
    validade = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["-emitido_em"]
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["emitido_por"]),
        ]

    def clean(self):
        super().clean()
        if self.inscricao.status != InscricaoStatus.CONFIRMADA:
            raise ValidationError({
                "inscricao": "Certificados só podem ser emitidos para inscrições confirmadas."
            })
        if not self.inscricao.presenca_confirmada:
            raise ValidationError({
                "inscricao": "Confirme a presença antes de emitir o certificado."
            })
        if self.emitido_por.perfil not in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
            raise ValidationError({
                "emitido_por": "Somente administradores ou organizadores podem emitir certificados."
            })

    def __str__(self):
        return f"Certificado {self.codigo} - {self.inscricao.participante}"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AcaoAuditoriaChoices(models.TextChoices):
    # User actions
    USUARIO_CRIADO = "USUARIO_CRIADO", "Usuário Criado"
    USUARIO_ATUALIZADO = "USUARIO_ATUALIZADO", "Usuário Atualizado"
    
    # Event actions
    EVENTO_CRIADO = "EVENTO_CRIADO", "Evento Criado"
    EVENTO_ATUALIZADO = "EVENTO_ATUALIZADO", "Evento Atualizado"
    EVENTO_EXCLUIDO = "EVENTO_EXCLUIDO", "Evento Excluído"
    EVENTO_CONSULTADO_API = "EVENTO_CONSULTADO_API", "Evento Consultado via API"
    
    # Inscricao actions
    INSCRICAO_CRIADA = "INSCRICAO_CRIADA", "Inscrição Criada"
    INSCRICAO_ATUALIZADA = "INSCRICAO_ATUALIZADA", "Inscrição Atualizada"
    INSCRICAO_CANCELADA = "INSCRICAO_CANCELADA", "Inscrição Cancelada"
    
    # Certificate actions
    CERTIFICADO_GERADO = "CERTIFICADO_GERADO", "Certificado Gerado"
    CERTIFICADO_CONSULTADO = "CERTIFICADO_CONSULTADO", "Certificado Consultado"
    CERTIFICADO_CONSULTADO_API = "CERTIFICADO_CONSULTADO_API", "Certificado Consultado via API"
    
    # Authentication actions
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"


class AuditLog(models.Model):
    """
    Audit log for tracking critical actions in the system.
    
    Tracks:
    - User creation
    - Event creation, updates, and deletion
    - API queries for events
    - Certificate generation and queries
    - Event inscriptions
    """
    acao = models.CharField(
        max_length=50,
        choices=AcaoAuditoriaChoices.choices,
        help_text="Tipo de ação realizada"
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_auditoria",
        help_text="Usuário que realizou a ação"
    )
    usuario_afetado = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_auditoria_afetado",
        help_text="Usuário afetado pela ação (ex: usuário criado)"
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_auditoria",
        help_text="Evento relacionado à ação"
    )
    inscricao = models.ForeignKey(
        Inscricao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_auditoria",
        help_text="Inscrição relacionada à ação"
    )
    certificado = models.ForeignKey(
        Certificado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_auditoria",
        help_text="Certificado relacionado à ação"
    )
    descricao = models.TextField(
        blank=True,
        help_text="Descrição detalhada da ação"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Endereço IP de onde a ação foi realizada"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="User agent do navegador/cliente"
    )
    dados_extras = models.JSONField(
        null=True,
        blank=True,
        help_text="Dados adicionais sobre a ação"
    )
    data_hora = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora da ação"
    )
    
    class Meta:
        ordering = ["-data_hora"]
        indexes = [
            models.Index(fields=["-data_hora"]),
            models.Index(fields=["acao"]),
            models.Index(fields=["usuario"]),
            models.Index(fields=["evento"]),
            models.Index(fields=["data_hora", "usuario"]),
            models.Index(fields=["data_hora", "evento"]),
        ]
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
    
    def __str__(self):
        usuario_nome = self.usuario.username if self.usuario else "Sistema"
        return f"{self.get_acao_display()} - {usuario_nome} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
