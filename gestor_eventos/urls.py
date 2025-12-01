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
    EmissaoCertificadoView,
    InscricaoUsuarioView,
    PresencaView,
    SignupView,
    logout_view,
)
from api.endpoints import EventoListView, InscricaoCreateView

urlpatterns = [
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/eventos/', EventoListView.as_view(), name='api-evento-list'),
    path('api/inscricao/', InscricaoCreateView.as_view(), name='api-inscricao-create'),
    
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
    path('admin/', admin.site.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
