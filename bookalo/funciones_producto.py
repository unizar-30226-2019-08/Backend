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
import itertools
from django.db.models import Count
import re
import unicodedata

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

def strip_accents(text):
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError): # unicode is a default on python 3 
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def GenericProducts(token,ultimo_indice,elementos_pagina):
	products = Producto.objects.filter(estado_venta=True).order_by('-num_likes')
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		products = itertools.islice(products, ultimo_indice, ultimo_indice + elementos_pagina)
	user = get_user(token)
	if user!=None:
		serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
	else:
		serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def ProductosUsuario(token, ultimo_indice, elementos_pagina, user_uid):
	if token != 'nothing':
		user = get_user(token)
	else:
		user = Usuario.objects.get(uid=user_uid)
	products = Producto.objects.filter(vendido_por=user)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		products = itertools.islice(products, ultimo_indice, ultimo_indice + elementos_pagina)
	serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
	return serializer

def ProductosFavoritos(token,ultimo_indice,elementos_pagina):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	products = Producto.objects.filter(le_gusta_a=user)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		products = itertools.islice(products, ultimo_indice, ultimo_indice + elementos_pagina)
	serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
	return serializer



def FiltradoProducto(biblio,token,ultimo_indice,elementos_pagina):
	tags = biblio['tags']
	user_latitude = biblio['user_latitude']
	user_longitude = biblio['user_longitude']
	max_distance = biblio['max_distance']
	min_price = biblio['min_price']
	max_price = biblio['max_price']
	min_score = biblio['min_score']
	#print(biblio)
	if int(min_score) == 0:
		min_score = '-1'
	search = biblio['busqueda']
	products_search = []

	if search != '-1' and search != '':
		preposiciones = ['a','ante','bajo','cabe','con','contra','de','desde','en','entre',
		'hacia','hasta','para','por','segun','sin','so','sobre','tras']
		
		for word in search.split():
			if word not in preposiciones:
				productos_palabra = Producto.objects.filter(nombre__contains=word)
				for producto in productos_palabra:
					products_search = products_search + [producto]

	if search == '-1' and user_latitude == '-1' and user_longitude == '-1' and max_distance == '-1' and min_price == '-1' and max_price == '-1' and min_score == '-1':
		return 'Bad request'

	if tags != '-1':
		#lista_tags = [x.strip() for x in tags.split(',')]
		#lista_tags = [re.sub('[^A-Za-z0-9áéíóúüñ]+', '', x) for x in lista_tags]
		#lista_tags = [x.translate(trans) for x in lista_tags]
		#lista_tags = [x.lower() for x in lista_tags]
		lista_tags = []
		#[print(x) for x in tags.split(',')]
		for x in tags.split(','):
			tag = x.strip()
			tag = re.sub('[^A-Za-z0-9á-źÁ-Źüñ]+', '', tag)
			tag = strip_accents(tag)
			tag = tag.lower()
			lista_tags.append(tag)
		#[print(x) for x in lista_tags]

		#print(lista_tags)
		tag_queryset = Tag.objects.filter(nombre__in=lista_tags)
		if min_price == '-1':
			if max_price == '-1':
				if min_score == '-1':
					products = Producto.objects.filter(tiene_tags__in=tag_queryset, estado_venta=True)
				else:
					products = Producto.objects.filter(vendido_por__media_valoraciones__gte=int(min_score), tiene_tags__in=tag_queryset, estado_venta=True)
			else:
				if min_score == '-1':
					products = Producto.objects.filter(precio__lte=Decimal(max_price), tiene_tags__in=tag_queryset, estado_venta=True)
				else:
					products = Producto.objects.filter(precio__lte=Decimal(max_price), vendido_por__media_valoraciones__gte=int(min_score), tiene_tags__in=tag_queryset, estado_venta=True)
		else:
			if max_price == '-1':
				if min_score == '-1':
					products = Producto.objects.filter(precio__gte=Decimal(min_price), tiene_tags__in=tag_queryset, estado_venta=True)
				else:
					products = Producto.objects.filter(precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=int(min_score), tiene_tags__in=tag_queryset, estado_venta=True)
			else:
				if min_score == '-1':
					products = Producto.objects.filter(precio__gte=Decimal(min_price), precio__lte=Decimal(max_price), tiene_tags__in=tag_queryset, estado_venta=True)
				else:
					products = Producto.objects.filter(precio__gte=Decimal(min_price), precio__lte=Decimal(max_price), vendido_por__media_valoraciones__gte=int(min_score), tiene_tags__in=tag_queryset, estado_venta=True)
	else:
		if min_price == '-1':
			if max_price == '-1':
				if min_score != '-1':
					products = Producto.objects.filter(vendido_por__media_valoraciones__gte=int(min_score), estado_venta=True)
			else:
				if min_score != '-1':
					products = Producto.objects.filter(precio__lte=Decimal(max_price), vendido_por__media_valoraciones__gte=int(min_score), estado_venta=True)
				else:
					products = Producto.objects.filter(precio__lte=Decimal(max_price), estado_venta=True)
		else:
			if max_price == '-1':
				if min_score != '-1':
					products = Producto.objects.filter(precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=int(min_score), estado_venta=True)
			else:
				if min_score != '-1':
					products = Producto.objects.filter(precio__gte=Decimal(min_price), precio__lte=Decimal(max_price), vendido_por__media_valoraciones__gte=int(min_score), estado_venta=True)
				else:
					products = Producto.objects.filter(precio__gte=Decimal(min_price), precio__lte=Decimal(max_price), estado_venta=True)

	#print(products)
	filtered_products = []
	if user_latitude != '-1' and user_longitude != '-1' and max_distance != '-1':
		#print("Voy a calcular distancias")
		for product in products:
			#print("Distancia maxima: " + max_distance)
			#print("Distancia calculada: " + str(calculate_distance(Decimal(product.latitud), Decimal(product.longitud), Decimal(user_latitude), Decimal(user_longitude))))
			#print(Decimal(user_latitude))
			#print(Decimal(user_longitude))
			#print(Decimal(product.latitud))
			#print(Decimal(product.longitud))
			if Decimal(max_distance) >= calculate_distance(Decimal(product.latitud), Decimal(product.longitud), Decimal(user_latitude), Decimal(user_longitude)):
				#print("Anyadido producto")
				filtered_products.append(product)
	else:
		for product in products:
			filtered_products.append(product)

	if search != '-1':
		#print("Voy a hacer la interseccion")
		#print(filtered_products)
		#print(products_search)
		final_product_list = set(filtered_products) & set(products_search)
		final_product_list = list(final_product_list)
		#print("He hecho la interseccion")
	else:
		final_product_list = filtered_products

	#print(final_product_list)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		final_product_list = itertools.islice(final_product_list, ultimo_indice, ultimo_indice + elementos_pagina)

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
	#Prueba si el precio es un numero o no
	try:
		precio = Decimal(precio)
	except:
		return 'Bad request'
	#Selecciona si el usuario ha creado el producto para enviar a domicilio o no
	if tipo_envio == 'True':
		tipo_envio = True
	else:
		tipo_envio = False
	#Selecciona el estado en el que se encuentra el producto, entre Nuevo, Seminuevo o Usado
	if estado_producto != 'Nuevo' and estado_producto != 'Seminuevo' and estado_producto != 'Usado':
		return 'Bad request'
	producto = Producto(vendido_por=user, 
						latitud=Decimal(latitud), 
						longitud=Decimal(longitud), 
						nombre=nombre, 
						precio=precio, 
						estado_producto=estado_producto, 
						estado_venta=True,
						tipo_envio=tipo_envio,
						descripcion=descripcion)
	producto.save()
	producto = Producto.objects.get(pk=producto.pk)
	print(producto)
	for tag in lista_tags:
		print(tag)
		tag_estandar = re.sub('[^A-Za-z0-9á-źÁ-Źüñ]+', '', tag)
		tag_estandar = strip_accents(tag_estandar)
		tag_estandar = tag_estandar.lower()
		producto.tiene_tags.get_or_create(nombre=tag_estandar)
	tags_in_producto = producto.tiene_tags.all()
	for tag in tags_in_producto:
		tag.number_of_uses = tag.number_of_uses + 1
		tag.save()
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
		validacion = ValidacionEstrella.objects.create(estrellas=stars, usuario_valorado=rated_user, usuario_que_valora=user, comentario=comment, producto=product)
		validacion.actualizar()
		return True
	except:
		return False

def GetTags(amount):
	try:
		if amount == 'all':
			sorted_tags = Tag.objects.all().order_by('-number_of_uses')
			return TagSerializer(sorted_tags, many=True).data
		else:
			sorted_tags = Tag.objects.all().order_by('-number_of_uses')[:amount]
			return TagSerializer(sorted_tags, many=True).data
	except:
		return None

def MarkAsSold(product_id, token):
	try:
		user = get_user(token)
		producto = Producto.objects.get(pk=int(product_id))
		if producto.vendido_por != user:
			return None
	except:
		return None
	try:
		Producto.objects.filter(pk=int(product_id)).update(estado_venta=False)
		return True
	except:
		return False