#######################################################
#	Proyecto Software 2018/19 - UNIZAR
#	Bookalo
#	11 de Marzo de 2019
#######################################################
#	AUTORES:
#	Palacios Gracia, Ignacio (739359)
#	Ubide Alaiz, David (736520)
#	Torres Sanchez, Enrique (734980)
#######################################################

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils.timezone import now as timezone_now
from enum import Enum
# 	'''
# 	Tag :
# 		nombre_tag          : String
#       es_predeterminado   : Booleano que indica si un tag es predeterminado o no
# 	'''

class Usuario(AbstractUser):
    uid = models.CharField(
        unique=True,
        max_length=100,
        verbose_name='UID del usuario en Firebase')
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del usuario asociado al login social')
    esta_baneado = models.BooleanField(
        default=False,
        verbose_name='Indica si un usuario ha llegado al limite de reportes y se le prohibe el acceso a la aplicacion')
    ultima_conexion = models.DateTimeField(
        default=timezone_now,
        verbose_name='Ultima conexion del usuario')
    latitud_registro = models.DecimalField(
        null=True,
        verbose_name='Latitud del usuario cuando se registro',
        max_digits=9,
        decimal_places=6)
    longitud_registro = models.DecimalField(
        null=True,
        verbose_name='Longitud del usuario cuando se registro',
        max_digits=9,
        decimal_places=6)
    media_valoraciones = models.IntegerField(
        default=-1,
        verbose_name='Media aritmetica de las valoraciones que ha recibido el usuario')
    imagen_perfil = models.CharField(
        max_length=200,
        verbose_name='URL de la imagen de perfil del usuario')

    def __str__(self):
        return self.uid + "/" + self.nombre

class Tag(models.Model):
    nombre = models.CharField(
        max_length=50,
        verbose_name='Nombre del tag')
    es_predeterminado = models.BooleanField(
        default=False,
        verbose_name='Marca si un tag ha sido creado por los administradores de la aplicacion')
    
    def __str__(self):
        return self.nombre

# 	'''
# 	EleccionEstadoProducto :
# 		tag = valor : 	Enumeración de los distintos posibles estados de un
#						producto.
# 	'''
class EleccionEstadoProducto(Enum):
	nuevo = "Nuevo"
	semi_nuevo = "Semi-nuevo"
	usado = "Usado"
	antiguo = "Antigüedad"
	roto = "Roto"
	desgastado = "Desgastado"

# 	'''
# 	EleccionEstadoVenta :
# 		tag = valor : 	Enumeración de los distintos posibles estados de una
#						venta.
# 	'''
class EleccionEstadoVenta(Enum):
	en_venta = "En venta"
	reservado = "Reservado"
	vendido = "Vendido"

# 	'''
# 	Producto :
# 		vendido_por : 	FK String
# 		latitud:		real
# 		longitud:		real
# 		nombre:			String
# 		precio:			String (Integer guardado como Char)
# 		estado_venta:	String (Únicamente Vendido,Reservado o en venta)
# 		tipo_envio:		String (TODO: Qué es)
# 		tiene_tags:		Tabla relación entre tags y producto. Asocia a
# 						cada producto una serie de tags creados previamente.
# 	'''

class Producto(models.Model):
    vendido_por = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Usuario que ha puesto a la venta el producto',
        related_name='producto_del_usuario')
    latitud = models.DecimalField(
        verbose_name='Latitud del producto',
        max_digits=9,
        decimal_places=6)
    longitud = models.DecimalField(
        verbose_name='Longitud del producto',
        max_digits=9,
        decimal_places=6)
    nombre = models.CharField(
        max_length=50,
        verbose_name='Nombre del producto')
    precio = models.DecimalField(
        verbose_name='Precio del producto',
        max_digits=9,
        decimal_places=2)
    estado_producto = models.CharField(
        max_length=50,
		choices=[(tag.name, tag.value) for tag in EleccionEstadoProducto],
        verbose_name='Estado en el que se encuentra el producto: Nuevo, Semi-nuevo, etc')
    estado_venta = models.CharField(
        max_length=50,
		choices=[(tag.name, tag.value) for tag in EleccionEstadoVenta],
        verbose_name='Estado en el que se encuentra la venta')
    num_acciones = models.IntegerField(
        default=0,
        verbose_name='Marca si uno o los dos usuarios han confirmado el estado de venta')
    tipo_envio = models.CharField(
        max_length=50,
        verbose_name='Si el usuario que ha colgado el producto esta dispuestos a enviar a domicilio o no')
    descripcion = models.CharField(
        max_length=1000,
        verbose_name='Descripcion asociada al producto')
    tiene_tags = models.ManyToManyField(
        Tag,
        blank=True,
        editable=True,
        related_name='tiene_tags')
    le_gusta_a = models.ManyToManyField(
        Usuario,
        blank=True,
        editable=True,
        related_name='le_gusta_a')
    num_likes = models.IntegerField(
        default=0,
        verbose_name='Likes acumulados por el producto')

    def __str__(self):
        return self.nombre

# 	'''
# 	Chat :
# 		vendedor:	String 	(PK de usuario)
# 		comprador:	String 	(PK de usuario)
# 		producto:	String	(PK de usuario)
# 	'''
#


class Chat(models.Model):
    vendedor = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Usuario que ha puesto a la venta el producto',
        related_name='vendedor')
    comprador = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Usuario que esta interesado en el producto',
        related_name='comprador')
    producto = models.ForeignKey(
        to=Producto,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Producto al que esta asociado el chat')
    
    def __str__(self):
        return str(self.vendedor) + "/" + str(self.comprador)

# 	'''
# 	Mensaje :
# 		texto:			String
# 		hora:			Date
# 		Chat_asociado:	ID	(PK de Chat)
# 	'''
#


class Mensaje(models.Model):
    texto = models.CharField(
        max_length=1000,
        verbose_name='Contenido del mensaje')
    hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Hora en la que se envio el mensaje')
    chat_asociado = models.ForeignKey(
        to=Chat,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Chat en el que se encuentra el mensaje',
        related_name='chat_del_mensaje')

    def __str__(self):
        return self.texto

# 	'''
# 	Report :
# 		identificador:		Integer
# 		Usuario_reportado:	String (PK de usuario)
# 		Causa:				String
# 	'''
#


class Report(models.Model):
    usuario_reportado = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Usuario que ha sido reportado',
        related_name='usuario_reportado')
    causa = models.CharField(
        max_length=1000,
        verbose_name='Causa del reporte')

    def __str__(self):
        return str(self.usuario_reportado) + "/" + self.causa

# 	'''
# 	Validación estrella :
# 		estrellas:			Integer
# 		usuario_valorado:	String (PK de usuario)
# 	'''
#


class ValidacionEstrella(models.Model):
    estrellas = models.IntegerField(
        verbose_name='Numero de estrellas que ha recibido')
    usuario_valorado = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        related_name='usuario_valorado_estrella',
        verbose_name='Usuario que ha sido valorado')
    usuario_que_valora = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        related_name='usuario_que_valora_estrella',
        verbose_name='Usuario que ha valorado al otro usuario')
    comentario = models.CharField(
        max_length=1000,
        verbose_name='Comentario de la valoracion')
    producto = models.ForeignKey(
        to=Producto,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Producto valorado')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.usuario_valorado) + "/" + str(self.usuario_que_valora)
# 	'''
# 	Contenido Multimedia :
# 		Contenido:	String (Indica el path del archivo)
# 		producto:	Integer (PK de producto)
# 	'''
#


class ContenidoMultimedia(models.Model):
    contenido = models.FileField(upload_to='media_files/')
    timestamp = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(
        to=Producto,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Producto al que pertenece el contenido multimedia',
        related_name='contenido_multimedia')
    orden_en_producto = models.IntegerField(
        default=0,
        verbose_name='Orden del contenido dentro del producto')

    def __str__(self):
        return self.contenido.url

class NotificacionesPendientes(models.Model):
    usuario_pendiente = models.ForeignKey(
        to=Usuario,
        null=False,
        on_delete=models.CASCADE,
        related_name='usuario_pendiente_notificacion',
        verbose_name='Usuario que tiene la notificación pendiente')

    descripcion_notificacion = models.CharField(
        max_length=1000,
        verbose_name='Texto de la notificacion')

    def __str__(self):
        return str(self.usuario_pendiente)