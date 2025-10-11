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
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='api/cadastro_usuario.html'), name='home'),
    path(
        'prototipos/cadastro-usuarios/',
        TemplateView.as_view(template_name='api/cadastro_usuario.html'),
        name='prototype-cadastro-usuario',
    ),
    path(
        'prototipos/cadastro-eventos/',
        TemplateView.as_view(template_name='api/cadastro_evento.html'),
        name='prototype-cadastro-evento',
    ),
    path(
        'prototipos/inscricao-usuarios/',
        TemplateView.as_view(template_name='api/inscricao_usuario.html'),
        name='prototype-inscricao-usuario',
    ),
    path(
        'prototipos/emissao-certificados/',
        TemplateView.as_view(template_name='api/emissao_certificado.html'),
        name='prototype-emissao-certificado',
    ),
    path(
        'prototipos/autenticacao/',
        TemplateView.as_view(template_name='api/autenticacao.html'),
        name='prototype-autenticacao',
    ),
    path('admin/', admin.site.urls),
]
