from bookalo.models import *
from rest_framework import serializers
from geopy import Nominatim
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class UserSerializer(serializers.HyperlinkedModelSerializer):
    ciudad = serializers.SerializerMethodField()
    conectado = serializers.SerializerMethodField()
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'ciudad', 'conectado')
    def get_ciudad(self, obj):
        geolocator = Nominatim(user_agent="bookalo")
        location = geolocator.reverse(str(obj.latitud_registro) + ',' + str(obj.longitud_registro))
        return location.raw['address']['city']
    
    def get_conectado(self, obj):
        ahora = timezone.now()
        result = relativedelta(ahora, obj.ultima_conexion)
        return result.days == 0 and result.hours == 0 and result.months == 0 and result.years == 0 and result.minutes < 5

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('nombre','es_predeterminado')

class MultimediaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContenidoMultimedia
        fields = ('contenido', 'orden_en_producto')

class MiniProductoSerializer(serializers.HyperlinkedModelSerializer):
    contenido_multimedia = serializers.SerializerMethodField()
    class Meta:
        model = Producto
        fields = ('nombre', 'precio', 'estado_venta', 'contenido_multimedia')

    def get_contenido_multimedia(self, obj):
        contenido = ContenidoMultimedia.objects.get(producto=obj.pk, orden_en_producto=0)
        return MultimediaSerializer(contenido)

class ProductoSerializer(serializers.HyperlinkedModelSerializer):
    vendido_por = UserSerializer(read_only=True)
    tiene_tags = TagSerializer(many=True, read_only=True)
    contenido_multimedia = serializers.SerializerMethodField()
    class Meta:
        model = Producto
        fields = ('nombre', 'precio', 'estado_producto', 'estado_venta', 'latitud', 'longitud', 'tipo_envio', 'descripcion', 'vendido_por', 'tiene_tags', 'num_likes', 'contenido_multimedia')

    def get_contenido_multimedia(self, obj):
        contenido = ContenidoMultimedia.objects.filter(producto=obj.pk).order_by('orden_en_producto')
        return MultimediaSerializer(contenido, many=True)

class ProductoSerializerList(serializers.HyperlinkedModelSerializer):
    vendido_por = UserSerializer(read_only=True)
    tiene_tags = TagSerializer(many=True, read_only=True)
    contenido_multimedia = MultimediaSerializer(many=True, read_only=True)
    class Meta:
        model = Producto
        fields = (('nombre', 'precio', 'estado_producto', 'estado_venta', 'latitud', 'longitud', 'tipo_envio', 'descripcion', 'vendido_por', 'tiene_tags', 'num_likes', 'contenido_multimedia'))


class ValidacionEstrellaSerializer(serializers.HyperlinkedModelSerializer):
    usuario_que_valora = UserSerializer(read_only=True)
    producto_asociado = serializers.SerializerMethodField()
    class Meta:
        model = ValidacionEstrella
        fields = ('estrellas', 'comentario', 'timestamp', 'usuario_que_valora', 'producto_asociado')

    def get_producto_asociado(self, obj):
        producto = Producto.objects.get(pk=obj.producto)
        return MiniProductoSerializer(producto)


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    usuario_valorado_estrella = serializers.SerializerMethodField()
    producto_del_usuario = ProductoSerializer(many=True, read_only=True)
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'esta_baneado', 'usuario_valorado_estrella', 'producto_del_usuario')

    def get_usuario_valorado_estrella(self, obj):
        validaciones = ValidacionEstrella.objects.filter(usuario_valorado=obj.pk).order_by('-timestamp')
        return ValidacionEstrellaSerializer(validaciones, many=True, read_only=True)

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    #usuario_reportado = serializers.SerializerMethodField()
    usuario_reportado = UserSerializer(read_only=True)
    class Meta:
        model = Report
        fields = ('usuario_reportado', 'causa')
