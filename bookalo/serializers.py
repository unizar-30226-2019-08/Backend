from bookalo.models import *
from rest_framework import serializers
from geopy import Nominatim
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class UserSerializer(serializers.HyperlinkedModelSerializer):
    ciudad = serializers.SerializerMethodField()
    conectado = serializers.SerializerMethodField()
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'ciudad', 'conectado', 'imagen_perfil')
    def get_ciudad(self, obj):
        geolocator = Nominatim(user_agent="bookalo")
        location = geolocator.reverse(str(obj.latitud_registro) + ',' + str(obj.longitud_registro))
        return location.raw['address']['city']
    
    def get_conectado(self, obj):
        ahora = datetime.now()
        ahora = ahora.replace(tzinfo=None)
        ultimaConexion = obj.ultima_conexion.replace(tzinfo=None)
        result = relativedelta(ahora, ultimaConexion)
        return result.days == 0 and result.hours == 0 and result.months == 0 and result.years == 0 and result.minutes < 5

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('nombre','es_predeterminado')

class MultimediaSerializer(serializers.HyperlinkedModelSerializer):
    contenido_url = serializers.SerializerMethodField()
    class Meta:
        model = ContenidoMultimedia
        fields = ('contenido_url', 'orden_en_producto')

    def get_contenido_url(self, obj):
        return obj.contenido.url

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
    valoracion_media_usuario = serializers.SerializerMethodField()
    class Meta:
        model = Producto
        fields = ('nombre', 'precio', 'estado_producto', 'estado_venta', 'latitud', 'longitud', 'tipo_envio', 'descripcion', 'vendido_por', 'tiene_tags', 'num_likes', 'contenido_multimedia')

    def get_contenido_multimedia(self, obj):
        contenido = ContenidoMultimedia.objects.filter(producto=obj.pk).order_by('orden_en_producto')
        return MultimediaSerializer(contenido, many=True)
    
    def get_valoracion_media_usuario(self, obj):
        return Usuario.objects.get(pk=obj.vendido_por).media_valoraciones

class ProductoSerializerList(serializers.HyperlinkedModelSerializer):
    vendido_por = UserSerializer(read_only=True)
    tiene_tags = TagSerializer(many=True, read_only=True)
    contenido_multimedia = MultimediaSerializer(many=True, read_only=True)
    class Meta:
        model = Producto
        fields = (('nombre', 'precio', 'estado_producto', 'estado_venta', 'latitud', 'longitud', 'tipo_envio', 'descripcion', 'vendido_por', 'tiene_tags', 'num_likes', 'contenido_multimedia'))


class ValidacionEstrellaSerializer(serializers.HyperlinkedModelSerializer):
    usuario_que_valora = UserSerializer(read_only=True)
    #producto_asociado = serializers.SerializerMethodField()
    producto_asociado = ProductoSerializerList(read_only=True, many=True)
    class Meta:
        model = ValidacionEstrella
        fields = ('estrellas', 'comentario', 'timestamp', 'usuario_que_valora', 'producto_asociado')

    def get_producto_asociado(self, obj):
        producto = Producto.objects.get(pk=obj.producto)
        return MiniProductoSerializer(producto)

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    usuario_valorado_estrella = serializers.SerializerMethodField()
    productos_favoritos = serializers.SerializerMethodField()
    producto_del_usuario = ProductoSerializerList(read_only=True, many=True)
    #usuario_valorado_estrella = ValidacionEstrellaSerializer(read_only=True, many=True)
    #productos_favoritos = ProductoSerializerList(read_only=True, many=True)
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'esta_baneado', 'usuario_valorado_estrella', 'producto_del_usuario', 'productos_favoritos')

    def get_usuario_valorado_estrella(self, obj):
        validaciones = ValidacionEstrella.objects.filter(usuario_valorado=obj.pk).order_by('-timestamp')
        return ValidacionEstrellaSerializer(validaciones, many=True, read_only=True).data
    
    def get_productos_favoritos(self, obj):
        favoritos = Producto.objects.filter(le_gusta_a__in=[obj.pk])
        return ProductoSerializer(favoritos, many=True, read_only=True).data

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    usuario_reportado = UserSerializer(read_only=True)
    class Meta:
        model = Report
        fields = ('usuario_reportado', 'causa')


class ChatSerializer(serializers.HyperlinkedModelSerializer):
    vendedor = UserSerializer(read_only=True)
    comprador = UserSerializer(read_only=True)
    producto = ProductoSerializerList(read_only=True)
    class Meta:
        model = Chat
        fields = ('vendedor', 'comprador', 'producto')
