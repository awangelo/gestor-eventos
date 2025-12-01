from rest_framework import serializers
from .models import Evento, Inscricao, Usuario

class OrganizadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email']

class EventoSerializer(serializers.ModelSerializer):
    organizador = OrganizadorSerializer(read_only=True)
    
    class Meta:
        model = Evento
        fields = ['id', 'titulo', 'tipo', 'data_inicio', 'data_fim', 'local', 'organizador']

class InscricaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscricao
        fields = ['evento']
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Inscricao.objects.create(participante=user, **validated_data)
