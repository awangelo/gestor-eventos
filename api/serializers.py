from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Evento, Inscricao, Usuario, Certificado, PerfilChoices, InscricaoStatus


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer for Usuario model."""
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'nome', 'email', 'telefone', 'instituicao', 'perfil']
        read_only_fields = ['id']


class OrganizadorSerializer(serializers.ModelSerializer):
    """Serializer for Organizador display in events."""
    
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email']


class ProfessorSerializer(serializers.ModelSerializer):
    """Serializer for Professor display in events."""
    
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'instituicao']


class EventoSerializer(serializers.ModelSerializer):
    """Serializer for Evento model."""
    
    organizador = OrganizadorSerializer(read_only=True)
    organizador_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(perfil__in=[PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]),
        source='organizador',
        write_only=True,
        required=False
    )
    professor_responsavel = ProfessorSerializer(read_only=True)
    professor_responsavel_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(perfil=PerfilChoices.PROFESSOR),
        source='professor_responsavel',
        write_only=True,
        required=False,
        allow_null=True
    )
    total_inscritos = serializers.IntegerField(read_only=True)
    vagas_disponiveis = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Evento
        fields = [
            'id', 'tipo', 'titulo', 'data_inicio', 'data_fim', 'horario',
            'local', 'capacidade', 'banner', 'organizador', 'organizador_id',
            'professor_responsavel', 'professor_responsavel_id',
            'total_inscritos', 'vagas_disponiveis', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'total_inscritos', 'vagas_disponiveis']
    
    def validate(self, attrs):
        """Validate evento data."""
        # If organizador not provided, use current user
        if 'organizador' not in attrs and self.context.get('request'):
            user = self.context['request'].user
            if user.perfil in [PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR]:
                attrs['organizador'] = user
        
        return attrs
    
    def create(self, validated_data):
        """Create evento with validation."""
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            )


class EventoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating events - only certain fields allowed."""
    
    class Meta:
        model = Evento
        fields = [
            'tipo', 'titulo', 'data_inicio', 'data_fim', 'horario',
            'local', 'capacidade', 'banner', 'professor_responsavel'
        ]
    
    def update(self, instance, validated_data):
        """Update evento with validation."""
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            )


class InscricaoSerializer(serializers.ModelSerializer):
    """Serializer for creating inscricoes (self-registration)."""
    
    evento_detalhes = EventoSerializer(source='evento', read_only=True)
    participante_detalhes = UsuarioSerializer(source='participante', read_only=True)
    
    class Meta:
        model = Inscricao
        fields = [
            'id', 'evento', 'evento_detalhes', 'participante', 'participante_detalhes',
            'status', 'data_inscricao', 'atualizado_em', 'presenca_confirmada'
        ]
        read_only_fields = ['id', 'participante', 'data_inscricao', 'atualizado_em', 'status', 'presenca_confirmada']
    
    def validate(self, attrs):
        """Validate inscricao data."""
        user = self.context['request'].user
        
        # Block Organizador from self-registration
        if user.perfil == PerfilChoices.ORGANIZADOR:
            raise serializers.ValidationError({
                'participante': 'Organizadores não podem se inscrever em eventos.'
            })
        
        # Only Aluno and Professor can register
        if user.perfil not in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
            raise serializers.ValidationError({
                'participante': 'Apenas alunos e professores podem se inscrever em eventos.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create inscricao with current user as participant."""
        user = self.context['request'].user
        validated_data['participante'] = user
        validated_data['status'] = InscricaoStatus.PENDENTE
        
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            )


class InscricaoManageSerializer(serializers.ModelSerializer):
    """Serializer for managing inscricoes (admin/organizador registering others)."""
    
    evento_detalhes = EventoSerializer(source='evento', read_only=True)
    participante_detalhes = UsuarioSerializer(source='participante', read_only=True)
    
    class Meta:
        model = Inscricao
        fields = [
            'id', 'evento', 'evento_detalhes', 'participante', 'participante_detalhes',
            'status', 'data_inscricao', 'atualizado_em', 'presenca_confirmada'
        ]
        read_only_fields = ['id', 'data_inscricao', 'atualizado_em']
    
    def validate_participante(self, value):
        """Validate that participante is Aluno or Professor."""
        if value.perfil not in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
            raise serializers.ValidationError(
                'Apenas alunos e professores podem ser inscritos em eventos.'
            )
        
        # Explicitly block Organizador
        if value.perfil == PerfilChoices.ORGANIZADOR:
            raise serializers.ValidationError(
                'Organizadores não podem ser inscritos em eventos.'
            )
        
        return value
    
    def validate(self, attrs):
        """Additional validation for inscricao management."""
        user = self.context['request'].user
        evento = attrs.get('evento')
        
        # Organizador can only manage inscricoes for their own events
        if user.perfil == PerfilChoices.ORGANIZADOR:
            if evento and evento.organizador != user:
                raise serializers.ValidationError({
                    'evento': 'Você só pode gerenciar inscrições dos seus próprios eventos.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create inscricao with validation."""
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            )
    
    def update(self, instance, validated_data):
        """Update inscricao with validation."""
        user = self.context['request'].user
        
        # Organizador can only update inscricoes for their own events
        if user.perfil == PerfilChoices.ORGANIZADOR:
            if instance.evento.organizador != user:
                raise serializers.ValidationError({
                    'detail': 'Você só pode atualizar inscrições dos seus próprios eventos.'
                })
        
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            )


class CertificadoSerializer(serializers.ModelSerializer):
    """Serializer for Certificado model."""
    
    inscricao_detalhes = InscricaoSerializer(source='inscricao', read_only=True)
    emitido_por_detalhes = UsuarioSerializer(source='emitido_por', read_only=True)
    participante_nome = serializers.CharField(source='inscricao.participante.nome', read_only=True)
    evento_titulo = serializers.CharField(source='inscricao.evento.titulo', read_only=True)
    evento_tipo = serializers.CharField(source='inscricao.evento.tipo', read_only=True)
    
    class Meta:
        model = Certificado
        fields = [
            'id', 'inscricao', 'inscricao_detalhes', 'emitido_por', 'emitido_por_detalhes',
            'carga_horaria', 'emitido_em', 'validade', 'observacoes',
            'participante_nome', 'evento_titulo', 'evento_tipo'
        ]
        read_only_fields = ['id', 'emitido_em']

