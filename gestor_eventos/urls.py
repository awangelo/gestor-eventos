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

from api.views import (
    AutenticacaoView,
    CadastroEventoView,
    CadastroUsuarioView,
    EmissaoCertificadoView,
    InscricaoUsuarioView,
)

urlpatterns = [
    path('', CadastroUsuarioView.as_view(), name='home'),
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
