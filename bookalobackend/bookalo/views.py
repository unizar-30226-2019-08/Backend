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

#Comprueba que el usuario este logeado en el sistema
def check_user_logged_in(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		user = Usuario.objects.get(uid=user_uid).update(ultima_conexion=datetime.now)
		return True
	except:
		return False

def update_last_connection(user):
	try:
		Usuario.objects.get(uid=user.uid).update(ultima_conexion=datetime.now())
		return True
	except:
		return False

def get_user(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		#user = Usuario.objects.get(uid=user_uid).update(ultima_conexion=datetime.now())
		user = Usuario.objects.get(uid=user_uid)
		user.update(ultima_conexion=datetime.now())
		return user
	except:
		return None

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

def index(request):
	return render(request, 'index.html')

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def Login(request, format=None):
	token = request.POST.get('token', 'nothing')
	latitud_registro = 0.0
	longitud_registro = 0.0
	g = GeoIP2()
	#ip = request.META.get('REMOTE_ADDR', None)
	#if ip:
	#	latitud_registro = g.city(ip)['latitude']
	#	longitud_registro = g.city(ip)['longitude']
	latitud_registro = 41.683490
	longitud_registro = -0.888479
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']
			name = user_info['users'][0]['email'].split("@")[0]
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)
		
		try:
			user = Usuario.objects.get(uid=user_uid)
			user.ultima_conexion = datetime.now()
			user.save(update_fields=['ultima_conexion'])

			if user.esta_baneado:
				return Response(UserSerializer(user).data, status=status.HTTP_401_UNAUTHORIZED)
			else:
				update_last_connection(user)
				return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

		except Usuario.DoesNotExist:
			new_user_data = Usuario.objects.create(uid=user_uid, nombre=name, latitud_registro=latitud_registro, longitud_registro=longitud_registro)
			return Response(UserSerializer(new_user_data).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def GenericProductView(request, format=None):
	if request.method != 'GET':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	try:
		products = Producto.objects.order_by('-num_likes')
		serializer = ProductoSerializerList(products, many=True, read_only=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
	except:
		return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
	


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GetUserProfile(request, format=None):
	token = request.POST.get('token', 'nothing')
	#auth.refresh(token)
	user_uid = request.POST.get('uid', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or user_uid == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		#if check_user_logged_in(token):
			#try:
				fetch_user = Usuario.objects.get(uid=user_uid)
				return Response(UserProfileSerializer(fetch_user).data, status=status.HTTP_200_OK)
			#except:
			#	return Response(status=status.HTTP_404_NOT_FOUND)
		#else:
		#	return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def SearchProduct(request, format=None):
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	preposiciones = ['a','ante','bajo','cabe','con','contra','de','desde','en','entre',
	'hacia','hasta','para','por','segun','sin','so','sobre','tras']
	try:
		search = request.POST.get('busqueda')
	except:
		return Response(status=status.HTTP_400_BAD_REQUEST)
	products = Producto.objects.none()
	try:
		for word in search.split():
			if word not in preposiciones:
				productos_palabra = Producto.objects.filter(nombre__contains=word)
				products = products | productos_palabra
		products.distinct()
		serializer = ProductoSerializerList(products, many=True, read_only=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
	except:
		return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def FilterProduct(request, format=None):
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	token = request.POST.get('token', 'nothing')
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			tags = request.POST.get('tags', '')

			user_latitude = request.POST.get('latitud', '')
			user_longitude = request.POST.get('longitud', '')
			max_distance = request.POST.get('distancia_maxima', '')
			min_price = request.POST.get('precio_minimo', '')
			max_price = request.POST.get('precio_maximo', '')
			min_score = request.POST.get('calificacion_minima', '')
			if tags == '' or user_latitude == '' or user_longitude == '' or max_distance == '' or min_price == '' or max_price == '' or min_score == '':
				return Response(status=status.HTTP_400_BAD_REQUEST)

			lista_tags = [x.strip() for x in tags.split(',')]
			tag_queryset = Tag.objects.filter(nombre__in=lista_tags)
			products = Producto.objects.filter(precio__lte=Decimal(max_price), precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=min_score, tiene_tags__in=tag_queryset)

			filtered_products = []
			for product in products:
				print(product.nombre)
				if Decimal(max_distance) >= calculate_distance(Decimal(product.latitud), Decimal(product.longitud), Decimal(user_latitude), Decimal(user_longitude)):
					filtered_products.append(product)
			serializer = ProductoSerializerList(filtered_products, many=True, read_only=True)
			return Response(serializer.data, status=status.HTTP_200_OK)
		except:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GetUserProducts(request, format=None):
	token = request.POST.get('token', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']
			user = Usuario.objects.get(uid=user_uid)
			products = Producto.objects.filter(vendido_por=user)
			serializer = ProductoSerializerList(products, many=True, read_only=True)
			return Response(serializer.data, status=status.HTTP_200_OK)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)

		

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateProduct(request, format=None):
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	token = request.POST.get('token', 'nothing')
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			#Cambiar esto
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']	
			user = Usuario.objects.get(uid=user_uid)
			if user == None:
				return Response(status=status.HTTP_404_NOT_FOUND)
			#Get all the required parameters for the product
			files = request.FILES.items()
			latitud = request.POST.get('latitud', '')
			longitud = request.POST.get('longitud', '')
			nombre = request.POST.get('nombre', '')
			precio = request.POST.get('precio', '')
			estado_producto = request.POST.get('estado_producto', '')
			tipo_envio = request.POST.get('tipo_envio', '')
			descripcion = request.POST.get('descripcion', '')
			tags = request.POST.get('tags', '')
			#Check that the request is correct
			if latitud == '' or longitud == '' or nombre == '' or precio == '' or estado_producto == '' or tipo_envio == '' or descripcion == '' or tags == '':
				return Response(status=status.HTTP_400_BAD_REQUEST)
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
			return Response(status=status.HTTP_201_CREATED)
		except:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateReport(request, format=None):
	token = request.POST.get('token', 'nothing')
	reporteduserUid = request.POST.get('uid', 'nothing')
	Comment = request.POST.get('comentario', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or reporteduserUid == 'nothing' or Comment == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			reporteduser = Usuario.objects.get(uid=reporteduserUid)
			reporte = Report.objects.create(usuario_reportado=reporteduser, causa=Comment)
			return Response(status=status.HTTP_201_CREATED)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateChat(request, format=None):
	token = request.POST.get('token', 'nothing')
	otroUserUid = request.POST.get('uidUsuario', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or otroUserUid == 'nothing' or productId == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']
			user = Usuario.objects.get(uid=user_uid)
			otroUser = Usuario.objects.get(uid=otroUserUid)
			product = Producto.objects.get(id=productId)
			chat = Chat.objects.create(vendedor=otroUser, comprador=user, producto=product)
			return Response(status=status.HTTP_201_CREATED)
			#return Response(ChatSerializer(chat).data, status=status.HTTP_200_OK)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)	


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def DeleteProduct(request, format=None):
	token = request.POST.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or productId == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']
			user = Usuario.objects.get(uid=user_uid)
			#Producto.objects.get(id=productId).delete()
			product = Producto.objects.get(id=productId)
			if product.vendido_por == user:
				product.delete()
				return Response(status=status.HTTP_200_OK)
			else:
				return Response(status=status.HTTP_401_UNAUTHORIZED)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)	

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def LikeProduct(request, format=None):
	token = request.POST.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or productId == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user = get_user(token)
			if user != None:
				product = Producto.objects.get(id=int(productId))
				product.num_likes = product.num_likes + 1
				product.le_gusta_a.add()
				product.save()
				return Response(status=status.HTTP_200_OK)
			else:
				return Response(status=status.HTTP_404_NOT_FOUND)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)
