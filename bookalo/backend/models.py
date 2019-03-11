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
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime

class Tag(models.Model):
    nombre = models.CharField(
        max_length = 50,
        verbose_name = 'Nombre del tag')

class Producto(models.Model):
    vendido_por = models.ForeignKey(
        to=User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Usuario que ha puesto a la venta el producto')
    latitud = models.DecimalField(
        verbose_name = 'Latitud del producto',
        max_digits = 9,
        decimal_places = 6)
    longitud = models.DecimalField(
        verbose_name = 'Longitud del producto',
        max_digits = 9,
        decimal_places = 6)
    nombre = models.CharField(
        max_length = 50,
        verbose_name = 'Nombre del producto')
    precio = models.CharField(
        max_length = 10,
        verbose_name = 'Precio del producto')
    estado_producto = models.CharField(
        max_length = 50,
        verbose_name = 'Estado en el que se encuentra el producto: Vendido, Reservado o En Venta')
    tipo_envio = models.CharField(
        max_length = 50,
        verbose_name = 'Si el usuario que ha colgado el producto esta dispuestos a enviar a domicilio o no')
    descripcion = models.CharField(
        max_length = 1000,
        verbose_name = 'Descripcion asociada al producto')
    tiene_tags = models.ManyToManyField(
        Tag,
        blank = True,
        editable = True,
        related_name = 'tiene_tags')

class Chat(models.Model):
    vendedor = models.ForeignKey(
        to=User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Usuario que ha puesto a la venta el producto')
    comprador = models.ForeignKey(
        to=User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Usuario que esta interesado en el producto')
    producto = models.ForeignKey(
        to=Producto,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Producto al que esta asociado el chat')

class Mensaje(models.Model):
    texto = models.CharField(
        max_length = 1000,
        verbose_name = 'Contenido del mensaje')
    hora = models.DateTimeField(
		auto_now_add=True,
		verbose_name='Hora en la que se envio el mensaje')
    chat_asociado = models.ForeignKey(
        to=Chat,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Chat en el que se encuentra el mensaje')

class Report(models.Model):
    identificador = models.IntegerField(
        unique = True,
        verbose_name = 'Identificador unico del report')
    usuario_reportado = models.ForeignKey(
        to=User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Usuario que ha sido reportado')
    causa = models.CharField(
        max_length = 1000,
        verbose_name = 'Causa del reporte')

class ValidacionProducto(models.Model):
    comentario = models.CharField(
        max_length = 1000,
        verbose_name = 'Comentario de la validacion')
    usuario_valorado = models.ForeignKey(
        to=User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Usuario que ha sido valorado')

class ValidacionEstrella(models.Model):
    estrellas = models.IntegerField(
        verbose_name = 'Numero de estrellas que ha recibido')
    usuario_valorado = models.ForeignKey(
        to=User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Usuario que ha sido valorado')

class ContenidoMultimedia(models.Model):
    contenido = models.FileField()
    producto = models.ForeignKey(
        to=Producto,
        null=False,
        on_delete=models.CASCADE,
        verbose_name = 'Producto al que pertenece el cotenido multimedia')


    