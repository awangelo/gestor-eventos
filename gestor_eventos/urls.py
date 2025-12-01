"""
URL configuration for gestor_eventos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

from api.views import (
    AutenticacaoView,
    CadastroEventoView,
    CadastroUsuarioView,
    DashboardView,
    DetalhesEventoView,
    EditarEventoView,
    DeletarEventoView,
    EmissaoCertificadoView,
    InscricaoUsuarioView,
    PresencaView,
    SignupView,
    logout_view,
)
from api.endpoints import (
    # Event endpoints
    EventoListView,
    EventoDetailView,
    EventoCreateView,
    EventoUpdateView,
    EventoDeleteView,
    # Inscricao endpoints
    InscricaoCreateView,
    InscricaoManageCreateView,
    MinhasInscricoesListView,
    InscricaoUpdateView,
    InscricaoCancelView,
    InscricaoDeleteView,
    # Certificado endpoints
    MeusCertificadosListView,
    CertificadoDetailView,
    # Management endpoints
    ParticipantesListView,
    EventoInscricoesListView,
    AuditLogView,
)

urlpatterns = [
    # ============================================================================
    # API ENDPOINTS
    # ============================================================================
    
    # Authentication
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    
    # Event management
    path('api/eventos/', EventoListView.as_view(), name='api-evento-list'),
    path('api/eventos/<int:pk>/', EventoDetailView.as_view(), name='api-evento-detail'),
    path('api/eventos/criar/', EventoCreateView.as_view(), name='api-evento-create'),
    path('api/eventos/<int:pk>/editar/', EventoUpdateView.as_view(), name='api-evento-update'),
    path('api/eventos/<int:pk>/deletar/', EventoDeleteView.as_view(), name='api-evento-delete'),
    
    # Inscricao management (self-registration)
    path('api/inscricoes/', MinhasInscricoesListView.as_view(), name='api-minhas-inscricoes'),
    path('api/inscricoes/criar/', InscricaoCreateView.as_view(), name='api-inscricao-create'),
    path('api/inscricoes/<int:pk>/cancelar/', InscricaoCancelView.as_view(), name='api-inscricao-cancel'),
    path('api/inscricoes/<int:pk>/deletar/', InscricaoDeleteView.as_view(), name='api-inscricao-delete'),
    
    # Inscricao management (admin/organizador managing others)
    path('api/inscricoes/gerenciar/', InscricaoManageCreateView.as_view(), name='api-inscricao-manage-create'),
    path('api/inscricoes/<int:pk>/gerenciar/', InscricaoUpdateView.as_view(), name='api-inscricao-manage-update'),
    
    # Event inscricoes (list all inscricoes for an event)
    path('api/eventos/<int:evento_id>/inscricoes/', EventoInscricoesListView.as_view(), name='api-evento-inscricoes'),
    
    # Certificados
    path('api/certificados/', MeusCertificadosListView.as_view(), name='api-meus-certificados'),
    path('api/certificados/<int:pk>/', CertificadoDetailView.as_view(), name='api-certificado-detail'),
    
    # Participants management
    path('api/participantes/', ParticipantesListView.as_view(), name='api-participantes-list'),
    
    # Audit logs
    path('api/audit/', AuditLogView.as_view(), name='api-audit-log'),
    
    # ============================================================================
    # WEB VIEWS
    # ============================================================================
    
    path('', AutenticacaoView.as_view(), name='home'),
    path('login/', AutenticacaoView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    path('cadastro-usuarios/', CadastroUsuarioView.as_view(), name='cadastro-usuario'),
    path('cadastro-eventos/', CadastroEventoView.as_view(), name='cadastro-evento'),
    path('inscricao/', InscricaoUsuarioView.as_view(), name='inscricao-usuario'),
    path('presenca/', PresencaView.as_view(), name='presenca'),
    path('certificados/', EmissaoCertificadoView.as_view(), name='emissao-certificado'),
    path('eventos/<int:evento_id>/', DetalhesEventoView.as_view(), name='detalhes-evento'),
    path('eventos/<int:evento_id>/editar/', EditarEventoView.as_view(), name='editar-evento'),
    path('eventos/<int:evento_id>/deletar/', DeletarEventoView.as_view(), name='deletar-evento'),
    
    # Prototypes (legacy)
    path(
        'prototipos/cadastro-usuarios/',
        CadastroUsuarioView.as_view(),
        name='prototype-cadastro-usuario',
    ),
    path(
        'prototipos/cadastro-eventos/',
        CadastroEventoView.as_view(),
        name='prototype-cadastro-evento',
    ),
    path(
        'prototipos/inscricao-usuarios/',
        InscricaoUsuarioView.as_view(),
        name='prototype-inscricao-usuario',
    ),
    path(
        'prototipos/emissao-certificados/',
        EmissaoCertificadoView.as_view(),
        name='prototype-emissao-certificado',
    ),
    path(
        'prototipos/autenticacao/',
        AutenticacaoView.as_view(),
        name='prototype-autenticacao',
    ),
    
    # Admin
    path('admin/', admin.site.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
