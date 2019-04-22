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


def GenericProducts():
	products = Producto.objects.order_by('-num_likes')
	serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def ProductosUsuario(token):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	products = Producto.objects.filter(vendido_por=user)
	serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def FiltradoProducto(biblio):
	tags = biblio['tags']
	user_latitude = biblio['user_latitude']
	user_longitude = biblio['user_longitude']
	max_distance = biblio['max_distance']
	min_price = biblio['min_price']
	max_price = biblio['max_price']
	min_score = biblio['min_score']
	search = biblio['busqueda']
	preposiciones = ['a','ante','bajo','cabe','con','contra','de','desde','en','entre',
	'hacia','hasta','para','por','segun','sin','so','sobre','tras']
	products_search = Producto.objects.none()
	for word in search.split():
		if word not in preposiciones:
			productos_palabra = Producto.objects.filter(nombre__contains=word)
			products_search = products_search | productos_palabra
	products_search.distinct()

	if tags == '' or user_latitude == '' or user_longitude == '' or max_distance == '' or min_price == '' or max_price == '' or min_score == '':
		return 'Bad request'

	lista_tags = [x.strip() for x in tags.split(',')]
	tag_queryset = Tag.objects.filter(nombre__in=lista_tags)
	products = Producto.objects.filter(precio__lte=Decimal(max_price), precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=min_score, tiene_tags__in=tag_queryset)

	filtered_products = []
	for product in products:
		print(product.nombre)
		if Decimal(max_distance) >= calculate_distance(Decimal(product.latitud), Decimal(product.longitud), Decimal(user_latitude), Decimal(user_longitude)):
			filtered_products.append(product)

	final_product_list = list(set(products_search) & set(filtered_products))
	serializer = ProductoSerializerList(final_product_list, many=True, read_only=True)
	return serializer


def CreacionProducto(biblio):
	token = biblio['token']
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']	
	user = Usuario.objects.get(uid=user_uid)
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
	tag_pk = []
	estado_producto = EleccionEstadoProducto(estado_producto)
	lista_tags = [x.strip() for x in tags.split(',')]
	for tag in lista_tags:
		tag_obj,created = Tag.objects.get_or_create(nombre=tag)
		tag_pk.append(tag_obj.pk)
	producto = Producto(vendido_por=user, 
						latitud=Decimal(latitud), 
						longitud=Decimal(longitud), 
						nombre=nombre, 
						precio=Decimal(precio), 
						estado_producto=estado_producto, 
						estado_venta=EleccionEstadoVenta.en_venta,
						tipo_envio=tipo_envio,
						descripcion=descripcion)
	producto.save()
	producto.tiene_tags.set(tag_pk)
	i = 0
	for file,created in files:
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
