from django.shortcuts import render, redirect
from bookalo.pyrebase_settings import db, auth
from bookalo.models import *
from bookalo.serializers import *
#from bookalo.functions import *
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from operator import itemgetter
from django.http import HttpResponse
from datetime import datetime, timedelta, timezone
from django.db.models import Q, Count
from django.contrib.gis.geoip2 import GeoIP2
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal
from .funciones_usuario import *

def calculate_distance(lat1, lon1, lat2, lon2):
	R = 6373.0
	lat1_rad = radians(lat1)
	lon1_rad = radians(lon1)
	lat2_rad = radians(lat2)
	lon2_rad = radians(lon2)

	dlon = lon2_rad - lon1_rad
	dlat = lat2_rad - lat1_rad
	a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	return R * c


def GenericProducts(token):
	products = Producto.objects.order_by('-num_likes')
	user = get_user(token)
	if user!=None:
		serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
	else:
		serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def ProductosUsuario(token):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	products = Producto.objects.filter(vendido_por=user)
	serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
	return serializer

def ProductosFavoritos(token):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	products = Producto.objects.filter(le_gusta_a=user)
	serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
	return serializer

def FiltradoProducto(biblio,token):
	tags = biblio['tags']
	user_latitude = biblio['user_latitude']
	user_longitude = biblio['user_longitude']
	max_distance = biblio['max_distance']
	min_price = biblio['min_price']
	max_price = biblio['max_price']
	min_score = biblio['min_score']
	if int(min_score) == 0:
		min_score = -1
	search = biblio['busqueda']
	products_search = []
	if search != 'nothing' and search != '':
		preposiciones = ['a','ante','bajo','cabe','con','contra','de','desde','en','entre',
		'hacia','hasta','para','por','segun','sin','so','sobre','tras']
		
		for word in search.split():
			if word not in preposiciones:
				productos_palabra = Producto.objects.filter(nombre__contains=word)
				for producto in productos_palabra:
					products_search = products_search + [producto]

	if user_latitude == '' or user_longitude == '' or max_distance == '' or min_price == '' or max_price == '' or min_score == '':
		return 'Bad request'
	if tags != '':
		lista_tags = [x.strip() for x in tags.split(',')]
		tag_queryset = Tag.objects.filter(nombre__in=lista_tags)
		products = Producto.objects.filter(precio__lte=Decimal(max_price), precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=min_score, tiene_tags__in=tag_queryset)
	else:
		products = Producto.objects.filter(precio__lte=Decimal(max_price), precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=min_score)
	filtered_products = []
	for product in products:
		if Decimal(max_distance) >= calculate_distance(Decimal(product.latitud), Decimal(product.longitud), Decimal(user_latitude), Decimal(user_longitude)):
			filtered_products.append(product)

	#final_product_list = list(set(products_search) & set(filtered_products))
	final_product_list =set(products_search).union(set(filtered_products))
	user = get_user(token)
	if user!=None:
		serializer = ProductoSerializerList(final_product_list, many=True, read_only=True, context = {"user": user})
	else:
		serializer = ProductoSerializerList(final_product_list, many=True, read_only=True)
	return serializer


def CreacionProducto(biblio):
	token = biblio['token']
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']	
	try:
		user = Usuario.objects.get(uid=user_uid)
	except:
		return 'Not found'
	if user == None:
		return 'Not found'
	#Get all the required parameters for the product
	files = biblio['files']
	latitud = biblio['latitud']
	longitud = biblio['longitud']
	nombre = biblio['nombre']
	precio = biblio['precio']
	estado_producto = biblio['estado_producto']
	tipo_envio = biblio['tipo_envio']
	descripcion = biblio['descripcion']
	tags = biblio['tags']
	#Check that the request is correct
	if latitud == '' or longitud == '' or nombre == '' or precio == '' or estado_producto == '' or tipo_envio == '' or descripcion == '' or tags == '':
		return 'Bad request'
	lista_tags = [x.strip() for x in tags.split(',')]
	#Selecciona si el usuario ha creado el producto para enviar a domicilio o no
	if tipo_envio == 'True':
		tipo_envio = True
	else:
		tipo_envio = False
	#Selecciona el estado en el que se encuentra el producto, entre Nuevo, Seminuevo o Usado
	try:
		estado_producto = EleccionEstadoProducto[estado_producto]
	except:
		return 'Bad request'
	producto = Producto(vendido_por=user, 
						latitud=Decimal(latitud), 
						longitud=Decimal(longitud), 
						nombre=nombre, 
						precio=Decimal(precio), 
						estado_producto=estado_producto, 
						estado_venta=True,
						tipo_envio=tipo_envio,
						descripcion=descripcion)
	producto.save()
	producto = Producto.objects.get(pk=producto.pk)
	for tag in lista_tags:
		producto.tiene_tags.get_or_create(nombre=tag)
	i = 0
	for file in files:
		multi = ContenidoMultimedia(contenido=file, producto=producto, orden_en_producto=i)
		multi.save()
		i = i + 1
	return 'Created'


def BorradoProducto(token,productId):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	product = Producto.objects.get(id=productId)
	if product.vendido_por == user:
		product.delete()
		return 'Ok'
		return Response(status=status.HTTP_200_OK)
	else:
		return 'Unauthorized'
		return Response(status=status.HTTP_401_UNAUTHORIZED)


def LikeProducto(token,productId):
	check_user_logged_in(token)
	user = get_user(token)
	if user != None:
		product = Producto.objects.get(id=int(productId))
		exists = Producto.objects.filter(id=int(productId), le_gusta_a=user)
		if exists.exists():
			product.le_gusta_a.remove(user)
			product.num_likes = product.num_likes - 1
		else:
			product.num_likes = product.num_likes + 1
			product.le_gusta_a.add(user)
		product.save()
		return 'OK'
	else:
		return 'NOT FOUND'

def GetProduct(product_pk,token):
	if product_pk == 'nothing':
		return 'NOT FOUND'
	try:
		product = Producto.objects.get(pk=int(product_pk))
		user = get_user(token)
		if user!=None:
			serializer = ProductoSerializerList(product, context = {"user": user})
		else:
			serializer = ProductoSerializerList(product)
		return serializer
	except:
		return 'NOT FOUND'

def ValorarVenta(token, rated_user_id, comment, product_id, stars):
	try:
		rated_user = Usuario.objects.get(uid=rated_user_id)
		user = get_user(token)
		product = Producto.objects.get(pk=int(product_id))
		ValidacionEstrella.objects.create(estrellas=stars, usuario_valorado=rated_user, usuario_que_valora=user, comentario=comment, producto=product)
		return True
	except:
		return False