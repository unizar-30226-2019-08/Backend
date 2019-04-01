from bookalo.models import *
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'access_token')

class ValidacionEstrellaSerializer(serializers.HyperlinkedModelSerializer):
    usuario_valorado = UserSerializer(read_only=True)
    usuario_que_valora = UserSerializer(read_only=True)
    class Meta:
        model = ValidacionEstrella
        fields = ('estrellas', 'usuario_valorado', 'usuario_que_valora')

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    valoraciones = ValidacionEstrellaSerializer(many=True, read_only=True)
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'valoraciones')

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('nombre')

class MultimediaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContenidoMultimedia
        fields = ('contenido')

class ProductoSerializer(serializers.HyperlinkedModelSerializer):
    vendido_por = UserSerializer(read_only=True)
    tiene_tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ('nombre', 'precio', 'estado_producto', 'latitud', 'longitud', 'tipo_envio', 'descripcion', 'vendido_por', 'tiene_tags', 'num_likes')

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Report
        fields = ('usuario_reportado', 'causa')