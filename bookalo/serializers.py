from bookalo.models import *
from rest_framework import serializers
#from geopy import Nominatim
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.timezone import now as timezone_now
from decimal import Decimal

class UserSerializer(serializers.HyperlinkedModelSerializer):
    conectado = serializers.SerializerMethodField()
    numValoraciones = serializers.SerializerMethodField()
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'ciudad', 'conectado', 'imagen_perfil', 'media_valoraciones', 'numValoraciones','ultima_conexion')
    
    def get_conectado(self, obj):
        ahora = timezone_now()
        ahora = ahora.replace(tzinfo=None)
        ultimaConexion = obj.ultima_conexion.replace(tzinfo=None)
        result = relativedelta(ahora, ultimaConexion)
        return result.days == 0 and result.hours == 0 and result.months == 0 and result.years == 0 and result.minutes < 5

    def get_numValoraciones(self,obj):
        return ValidacionEstrella.objects.filter(usuario_valorado=obj).count()

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('nombre',)

class MultimediaSerializer(serializers.HyperlinkedModelSerializer):
    contenido_url = serializers.SerializerMethodField()
    class Meta:
        model = ContenidoMultimedia
        fields = ('contenido_url',)

    def get_contenido_url(self, obj):
        return obj.contenido.url

class MiniProductoSerializer(serializers.HyperlinkedModelSerializer):
    contenido_multimedia = serializers.SerializerMethodField()
    precio = serializers.SerializerMethodField()
    class Meta:
        model = Producto
        fields = ('pk','nombre', 'precio', 'estado_venta', 'contenido_multimedia')

    def get_contenido_multimedia(self, obj):
        contenido = ContenidoMultimedia.objects.get(producto=obj.pk, orden_en_producto=0)
        return MultimediaSerializer(contenido)

    def get_precio(self,obj):
        return Decimal(obj.precio)

class ProductoSerializer(serializers.HyperlinkedModelSerializer):
    tiene_tags = TagSerializer(many=True, read_only=True)
    contenido_multimedia = serializers.SerializerMethodField()
    valoracion_media_usuario = serializers.SerializerMethodField()
    precio = serializers.SerializerMethodField()
    latitud = serializers.SerializerMethodField()
    longitud = serializers.SerializerMethodField()
    class Meta:
        model = Producto
        fields = ('pk','nombre', 'precio', 'estado_producto', 'estado_venta','valoracion_media_usuario',
         'latitud', 'longitud', 'tipo_envio', 'descripcion', 'tiene_tags',
          'num_likes', 'contenido_multimedia', 'isbn')

    def get_contenido_multimedia(self, obj):
        contenido = ContenidoMultimedia.objects.filter(producto=obj.pk).order_by('orden_en_producto')
        return MultimediaSerializer(contenido, many=True).data
    
    def get_valoracion_media_usuario(self, obj):
        return Usuario.objects.get(pk=obj.vendido_por.pk).media_valoraciones

    def get_precio(self,obj):
        return Decimal(obj.precio)

    def get_latitud(self,obj):
        return Decimal(obj.latitud)

    def get_longitud(self,obj):
        return Decimal(obj.longitud)


class ProductoSerializerList(serializers.HyperlinkedModelSerializer):
    vendido_por = UserSerializer(read_only=True)
    le_gusta = serializers.SerializerMethodField()
    info_producto = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = ('pk','le_gusta', 'vendido_por', 'info_producto')

    def get_le_gusta(self, obj):
        usuario = self.context.get('user', 'nothing')
        if usuario in obj.le_gusta_a.all():
            return True
        else:
            return False
    
    def get_info_producto(self, obj):
        prod = Producto.objects.get(pk = obj.pk)
        return ProductoSerializer(prod, read_only=True).data

class ValidacionEstrellaSerializer(serializers.HyperlinkedModelSerializer):
    usuario_que_valora = UserSerializer(read_only=True)
    producto = ProductoSerializer(read_only=True)
    compra_o_venta = serializers.SerializerMethodField()
    class Meta:
        model = ValidacionEstrella
        fields = ('pk','estrellas', 'comentario', 'compra_o_venta','timestamp', 'usuario_que_valora', 'producto')

    def get_producto_asociado(self,obj):
        product = Producto.objects.get(pk=self.producto.pk)
        return MiniProductoSerializer(product, read_only=True).data

    def get_compra_o_venta(self,obj):
    	usuario = self.context.get('user', 'nothing')
    	producto = obj.producto
    	if producto.vendido_por == usuario:
    		tipo = 'Venta'
    	else:
    		tipo = 'Compra'
    	return tipo
    	

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    productos_favoritos = serializers.SerializerMethodField()
    producto_del_usuario = ProductoSerializerList(read_only=True, many=True)
    class Meta:
        model = Usuario
        fields = ('uid', 'nombre', 'imagen_perfil','media_valoraciones','esta_baneado', 
            'producto_del_usuario', 'productos_favoritos')

    def get_usuario_valorado_estrella(self, obj):
        validaciones = ValidacionEstrella.objects.filter(usuario_valorado=obj.pk).order_by('-timestamp')
        return ValidacionEstrellaSerializer(validaciones, many=True, read_only=True).data
    
    def get_productos_favoritos(self, obj):
        favoritos = Producto.objects.filter(le_gusta_a__in=[obj.pk])
        return ProductoSerializerList(favoritos, many=True, read_only=True).data


class ReportSerializer(serializers.HyperlinkedModelSerializer):
    usuario_reportado = UserSerializer(read_only=True)
    class Meta:
        model = Report
        fields = ('pk','usuario_reportado', 'causa', 'comentario')


class ChatSerializer(serializers.HyperlinkedModelSerializer):
    vendedor = UserSerializer(read_only=True)
    comprador = UserSerializer(read_only=True)
    producto = ProductoSerializerList(read_only=True)
    class Meta:
        model = Chat
        fields = ('pk','vendedor', 'comprador', 'producto')

class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    #usuario_pendiente = UserSerializer(read_only=True)
    producto = ProductoSerializerList(read_only=True)
    otro_usuario_compra = UserSerializer(read_only=True)
    class Meta:
        model = NotificacionesPendientes
        fields = ('producto', 'otro_usuario_compra','descripcion_notificacion')


class MensajeSerializer(serializers.HyperlinkedModelSerializer):
    es_suyo = serializers.SerializerMethodField()
    class Meta:
        model = Mensaje
        fields = ('texto', 'hora', 'es_suyo')

    def get_es_suyo(self, obj):
        print("He comprobado si era suyo")
        usuario = self.context.get('user', 'nothing')
        if obj.emisor == usuario:
            return True
        else:
            return False