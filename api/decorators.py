from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .models import PerfilChoices


def perfil_required(*perfis_permitidos):
    """
    Decorator to restrict view access based on user profile.
    Usage: @perfil_required(PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'perfil'):
                messages.error(request, "Usuário sem perfil definido.")
                return redirect('login')
            
            if request.user.perfil not in perfis_permitidos:
                messages.error(request, "Você não tem permissão para acessar esta página.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator to restrict view to ADMIN users only."""
    return perfil_required(PerfilChoices.ADMIN)(view_func)


def organizador_or_admin_required(view_func):
    """Decorator to restrict view to ORGANIZADOR or ADMIN users."""
    return perfil_required(PerfilChoices.ADMIN, PerfilChoices.ORGANIZADOR)(view_func)


def aluno_professor_required(view_func):
    """Decorator to restrict view to ALUNO or PROFESSOR users."""
    return perfil_required(PerfilChoices.ALUNO, PerfilChoices.PROFESSOR)(view_func)
