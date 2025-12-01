"""
Custom permissions for the API.

Business rules:
- Aluno e Professor: Can register for events, cancel registrations, and view their certificates
- Organizador: Can create, update, delete events, register participants, view audit logs
- Organizador: CANNOT register themselves for events
- Admin: Has all permissions
"""

from rest_framework import permissions
from .models import PerfilChoices


class IsAluno(permissions.BasePermission):
    """Permission for Aluno users only."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil == PerfilChoices.ALUNO
        )


class IsProfessor(permissions.BasePermission):
    """Permission for Professor users only."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil == PerfilChoices.PROFESSOR
        )


class IsOrganizador(permissions.BasePermission):
    """Permission for Organizador users only."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil == PerfilChoices.ORGANIZADOR
        )


class IsAdmin(permissions.BasePermission):
    """Permission for Admin users only."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil == PerfilChoices.ADMIN
        )


class IsAlunoOrProfessor(permissions.BasePermission):
    """Permission for Aluno or Professor users."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]
        )


class IsOrganizadorOrAdmin(permissions.BasePermission):
    """Permission for Organizador or Admin users."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil in [PerfilChoices.ORGANIZADOR, PerfilChoices.ADMIN]
        )


class CanManageEvents(permissions.BasePermission):
    """
    Permission to manage events.
    - Admin can manage all events
    - Organizador can only manage their own events
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil in [PerfilChoices.ORGANIZADOR, PerfilChoices.ADMIN]
        )
    
    def has_object_permission(self, request, view, obj):
        # Admin can manage any event
        if request.user.perfil == PerfilChoices.ADMIN:
            return True
        
        # Organizador can only manage their own events
        if request.user.perfil == PerfilChoices.ORGANIZADOR:
            return obj.organizador == request.user
        
        return False


class CanRegisterForEvents(permissions.BasePermission):
    """
    Permission to register for events.
    Only Aluno and Professor can register for events.
    Organizador CANNOT register for events.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil in [PerfilChoices.ALUNO, PerfilChoices.PROFESSOR]
        )


class CanManageInscricoes(permissions.BasePermission):
    """
    Permission to manage inscricoes (register others).
    - Admin and Organizador can register participants
    - Organizador can only manage inscricoes for their own events
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'perfil') and
            request.user.perfil in [PerfilChoices.ORGANIZADOR, PerfilChoices.ADMIN]
        )


class CanViewOwnInscricoes(permissions.BasePermission):
    """
    Permission to view own inscricoes.
    Users can only view their own inscricoes.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Users can only access their own inscricoes
        return obj.participante == request.user


class CanCancelInscricao(permissions.BasePermission):
    """
    Permission to cancel an inscricao.
    - Aluno/Professor can cancel their own inscricoes
    - Admin/Organizador can cancel any inscricao (for their events)
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Own inscricao
        if obj.participante == request.user:
            return True
        
        # Admin can cancel any
        if request.user.perfil == PerfilChoices.ADMIN:
            return True
        
        # Organizador can cancel for their events
        if request.user.perfil == PerfilChoices.ORGANIZADOR:
            return obj.evento.organizador == request.user
        
        return False


class CanViewCertificados(permissions.BasePermission):
    """
    Permission to view certificados.
    - Aluno/Professor can view their own certificados
    - Admin/Organizador can view certificados for their events
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Own certificado
        if obj.inscricao.participante == request.user:
            return True
        
        # Admin can view any
        if request.user.perfil == PerfilChoices.ADMIN:
            return True
        
        # Organizador can view for their events
        if request.user.perfil == PerfilChoices.ORGANIZADOR:
            return obj.inscricao.evento.organizador == request.user
        
        return False
