"""
REST API endpoints for the event management system.

Business rules implemented:
- Aluno e Professor: Can register for events, cancel registrations, view their certificates
- Organizador: Can create/update/delete events, register participants, view audit logs
- Organizador: CANNOT register themselves for events
- Admin: Has all permissions
"""

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Evento, Inscricao, Usuario, Certificado, PerfilChoices, InscricaoStatus
from .serializers import (
    EventoSerializer,
    EventoUpdateSerializer,
    InscricaoSerializer,
    InscricaoManageSerializer,
    CertificadoSerializer,
    UsuarioSerializer,
)
from .permissions import (
    CanRegisterForEvents,
    CanManageEvents,
    CanManageInscricoes,
    CanCancelInscricao,
    CanViewCertificados,
    IsOrganizadorOrAdmin,
    IsAlunoOrProfessor,
)
from .audit import (
    log_evento_criado,
    log_evento_atualizado,
    log_evento_excluido,
    log_evento_consultado_api,
    log_inscricao_criada,
    log_inscricao_atualizada,
    log_certificado_consultado,
)


# ============================================================================
# EVENT ENDPOINTS
# ============================================================================

class EventoListView(generics.ListAPIView):
    """
    List all events.
    All authenticated users can view events.
    """
    serializer_class = EventoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter events based on user role."""
        user = self.request.user
        
        # Log API query
        log_evento_consultado_api(self.request)
        
        # Aluno and Professor see all events
        if user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
            return Evento.objects.all().select_related('organizador', 'professor_responsavel')
        
        # Organizador sees only their events
        elif user.perfil == PerfilChoices.ORGANIZADOR:
            return Evento.objects.filter(organizador=user).select_related('organizador', 'professor_responsavel')
        
        # Admin sees all events
        else:
            return Evento.objects.all().select_related('organizador', 'professor_responsavel')


class EventoDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific event.
    All authenticated users can view event details.
    """
    serializer_class = EventoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter events based on user role."""
        user = self.request.user
        
        if user.perfil == PerfilChoices.ORGANIZADOR:
            # Organizador can only view their own events
            return Evento.objects.filter(organizador=user).select_related('organizador', 'professor_responsavel')
        
        return Evento.objects.all().select_related('organizador', 'professor_responsavel')
    
    def retrieve(self, request, *args, **kwargs):
        """Override to log API access."""
        instance = self.get_object()
        log_evento_consultado_api(request, instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class EventoCreateView(generics.CreateAPIView):
    """
    Create a new event.
    Only Organizador and Admin can create events.
    """
    serializer_class = EventoSerializer
    permission_classes = [IsOrganizadorOrAdmin]
    
    def perform_create(self, serializer):
        try:
            evento = serializer.save()
            # Log event creation
            log_evento_criado(self.request, evento)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})


class EventoUpdateView(generics.UpdateAPIView):
    """
    Update an event.
    - Admin can update any event
    - Organizador can only update their own events
    """
    serializer_class = EventoUpdateSerializer
    permission_classes = [CanManageEvents]
    
    def get_queryset(self):
        """Filter events based on user role."""
        user = self.request.user
        
        if user.perfil == PerfilChoices.ORGANIZADOR:
            return Evento.objects.filter(organizador=user)
        
        return Evento.objects.all()
    
    def perform_update(self, serializer):
        try:
            # Get original instance to track changes
            instance = serializer.instance
            # Save changes
            evento = serializer.save()
            
            # Log update
            campos_alterados = list(serializer.validated_data.keys()) if serializer.validated_data else []
            log_evento_atualizado(self.request, evento, campos_alterados)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})


class EventoDeleteView(generics.DestroyAPIView):
    """
    Delete an event.
    - Admin can delete any event
    - Organizador can only delete their own events
    """
    permission_classes = [CanManageEvents]
    
    def get_queryset(self):
        """Filter events based on user role."""
        user = self.request.user
        
        if user.perfil == PerfilChoices.ORGANIZADOR:
            return Evento.objects.filter(organizador=user)
        
        return Evento.objects.all()
    
    def perform_destroy(self, instance):
        """Log deletion before destroying."""
        # Capture event info before deletion
        evento_info = {
            'id': instance.id,
            'tipo': instance.tipo,
            'titulo': instance.titulo,
            'local': instance.local,
            'data_inicio': instance.data_inicio.isoformat(),
            'data_fim': instance.data_fim.isoformat() if instance.data_fim else None,
        }
        
        # Delete the instance
        instance.delete()
        
        # Log after successful deletion
        log_evento_excluido(self.request, evento_info)


# ============================================================================
# INSCRICAO ENDPOINTS
# ============================================================================

class InscricaoCreateView(generics.CreateAPIView):
    """
    Create a new inscricao (self-registration).
    Only Aluno and Professor can register themselves for events.
    Organizador CANNOT register for events.
    """
    serializer_class = InscricaoSerializer
    permission_classes = [CanRegisterForEvents]
    
    def perform_create(self, serializer):
        # Double-check that user is not Organizador
        if self.request.user.perfil == PerfilChoices.ORGANIZADOR:
            raise PermissionDenied('Organizadores não podem se inscrever em eventos.')
        
        try:
            inscricao = serializer.save()
            # Log self-registration
            log_inscricao_criada(self.request, inscricao)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})


class InscricaoManageCreateView(generics.CreateAPIView):
    """
    Register a participant for an event (admin/organizador registering others).
    Only Admin and Organizador can use this endpoint.
    Organizador can only register participants for their own events.
    """
    serializer_class = InscricaoManageSerializer
    permission_classes = [CanManageInscricoes]
    
    def perform_create(self, serializer):
        try:
            inscricao = serializer.save()
            # Log managed registration
            log_inscricao_criada(self.request, inscricao)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})


class MinhasInscricoesListView(generics.ListAPIView):
    """
    List current user's inscricoes.
    Aluno and Professor can view their own inscricoes.
    """
    serializer_class = InscricaoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get inscricoes for current user."""
        return Inscricao.objects.filter(
            participante=self.request.user
        ).select_related('evento', 'evento__organizador', 'participante')


class InscricaoUpdateView(generics.UpdateAPIView):
    """
    Update an inscricao (for admin/organizador to change status, presence, etc.).
    - Admin can update any inscricao
    - Organizador can only update inscricoes for their events
    """
    serializer_class = InscricaoManageSerializer
    permission_classes = [CanManageInscricoes]
    
    def get_queryset(self):
        """Filter inscricoes based on user role."""
        user = self.request.user
        
        if user.perfil == PerfilChoices.ORGANIZADOR:
            return Inscricao.objects.filter(evento__organizador=user)
        
        return Inscricao.objects.all()
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})


class InscricaoCancelView(APIView):
    """
    Cancel an inscricao.
    - Aluno/Professor can cancel their own inscricoes
    - Admin can cancel any inscricao
    - Organizador can cancel inscricoes for their events
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        inscricao = get_object_or_404(Inscricao, pk=pk)
        
        # Check permission
        user = request.user
        can_cancel = False
        
        # Own inscricao
        if inscricao.participante == user:
            can_cancel = True
        # Admin can cancel any
        elif user.perfil == PerfilChoices.ADMIN:
            can_cancel = True
        # Organizador can cancel for their events
        elif user.perfil == PerfilChoices.ORGANIZADOR and inscricao.evento.organizador == user:
            can_cancel = True
        
        if not can_cancel:
            raise PermissionDenied('Você não tem permissão para cancelar esta inscrição.')
        
        # Update status to CANCELADA
        inscricao.status = InscricaoStatus.CANCELADA
        inscricao.save()
        
        serializer = InscricaoSerializer(inscricao)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InscricaoDeleteView(generics.DestroyAPIView):
    """
    Delete an inscricao completely.
    - Aluno/Professor can delete their own inscricoes
    - Admin can delete any inscricao
    - Organizador can delete inscricoes for their events
    """
    permission_classes = [CanCancelInscricao]
    
    def get_queryset(self):
        """Filter inscricoes based on permissions."""
        user = self.request.user
        
        # Own inscricoes
        if user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
            return Inscricao.objects.filter(participante=user)
        
        # Organizador's events
        elif user.perfil == PerfilChoices.ORGANIZADOR:
            return Inscricao.objects.filter(evento__organizador=user)
        
        # Admin can delete any
        return Inscricao.objects.all()


# ============================================================================
# CERTIFICADO ENDPOINTS
# ============================================================================

class MeusCertificadosListView(generics.ListAPIView):
    """
    List current user's certificados.
    Aluno and Professor can view their own certificados.
    """
    serializer_class = CertificadoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get certificados for current user."""
        return Certificado.objects.filter(
            inscricao__participante=self.request.user
        ).select_related('inscricao', 'inscricao__evento', 'inscricao__participante', 'emitido_por')


class CertificadoDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific certificado.
    - Owner can view their own certificado
    - Admin can view any certificado
    - Organizador can view certificados for their events
    """
    serializer_class = CertificadoSerializer
    permission_classes = [CanViewCertificados]
    
    def get_queryset(self):
        """Filter certificados based on user role."""
        user = self.request.user
        
        # Own certificados
        if user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]:
            return Certificado.objects.filter(inscricao__participante=user)
        
        # Organizador's events
        elif user.perfil == PerfilChoices.ORGANIZADOR:
            return Certificado.objects.filter(inscricao__evento__organizador=user)
        
        # Admin can view any
        return Certificado.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """Override to log API access."""
        instance = self.get_object()
        log_certificado_consultado(request, instance, via_api=True)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Override to log certificate access."""
        instance = self.get_object()
        log_certificado_consultado(request, instance, via_api=True)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================================================================
# PARTICIPANT MANAGEMENT ENDPOINTS
# ============================================================================

class ParticipantesListView(generics.ListAPIView):
    """
    List all participants (Aluno and Professor).
    Only Admin and Organizador can view this list.
    """
    serializer_class = UsuarioSerializer
    permission_classes = [IsOrganizadorOrAdmin]
    
    def get_queryset(self):
        """Get all participants (Aluno and Professor)."""
        return Usuario.objects.filter(
            perfil__in=[PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]
        ).order_by('nome')


class EventoInscricoesListView(generics.ListAPIView):
    """
    List all inscricoes for a specific event.
    - Admin can view inscricoes for any event
    - Organizador can only view inscricoes for their events
    """
    serializer_class = InscricaoSerializer
    permission_classes = [IsOrganizadorOrAdmin]
    
    def get_queryset(self):
        """Get inscricoes for the specified event."""
        evento_id = self.kwargs.get('evento_id')
        user = self.request.user
        
        # Verify access to event
        if user.perfil == PerfilChoices.ORGANIZADOR:
            evento = get_object_or_404(Evento, pk=evento_id, organizador=user)
        else:
            evento = get_object_or_404(Evento, pk=evento_id)
        
        return Inscricao.objects.filter(evento=evento).select_related('participante', 'evento')


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

class AuditLogView(APIView):
    """
    View audit logs.
    Only Admin and Organizador can view audit logs.
    
    Note: This is a placeholder. Implement proper audit logging model if needed.
    For now, returns basic activity information from existing models.
    """
    permission_classes = [IsOrganizadorOrAdmin]
    
    def get(self, request):
        user = request.user
        
        audit_data = {
            'user': user.username,
            'perfil': user.perfil,
            'logs': []
        }
        
        # Get recent events
        if user.perfil == PerfilChoices.ORGANIZADOR:
            eventos = Evento.objects.filter(organizador=user).order_by('-criado_em')[:10]
        else:
            eventos = Evento.objects.all().order_by('-criado_em')[:10]
        
        for evento in eventos:
            audit_data['logs'].append({
                'type': 'evento_criado',
                'timestamp': evento.criado_em,
                'details': f'Evento "{evento.titulo or evento.tipo}" criado',
                'organizador': evento.organizador.nome
            })
        
        # Get recent inscricoes
        if user.perfil == PerfilChoices.ORGANIZADOR:
            inscricoes = Inscricao.objects.filter(evento__organizador=user).order_by('-data_inscricao')[:10]
        else:
            inscricoes = Inscricao.objects.all().order_by('-data_inscricao')[:10]
        
        for inscricao in inscricoes:
            audit_data['logs'].append({
                'type': 'inscricao_criada',
                'timestamp': inscricao.data_inscricao,
                'details': f'{inscricao.participante.nome} inscrito em {inscricao.evento.titulo or inscricao.evento.tipo}',
                'status': inscricao.status
            })
        
        # Sort logs by timestamp
        audit_data['logs'] = sorted(audit_data['logs'], key=lambda x: x['timestamp'], reverse=True)
        
        return Response(audit_data, status=status.HTTP_200_OK)

