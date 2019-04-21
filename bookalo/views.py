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
from .funciones_producto import *
from .funciones_chat import *
from .funciones_report import *

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



def index(request):
	return render(request, 'bookalo/index.html')

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
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if request.method != 'GET':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	try:
		serializer = GenericProducts()
		if movil == 'true':
			return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
		else:
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
		
	


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
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	search = request.POST.get('busqueda', 'nothing')
	if search == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
	try:
		serializer = BusquedaProducto(search)
		if movil == 'true':
			return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
		else:
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
			return render(request, 'bookalo/index.html', {'productos': serializer.data})



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def FilterProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
	token = request.POST.get('token', 'nothing')
	if token == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
	else:
		try:
			tags = request.POST.get('tags', '')
			user_latitude = request.POST.get('latitud', '')
			user_longitude = request.POST.get('longitud', '')
			max_distance = request.POST.get('distancia_maxima', '')
			min_price = request.POST.get('precio_minimo', '')
			max_price = request.POST.get('precio_maximo', '')
			min_score = request.POST.get('calificacion_minima', '')
			biblioteca = {'tags':tags, 'user_latitude':user_latitude, 'user_longitude':user_longitude, 'max_distance':max_distance,
						'min_price':min_price,'max_price':max_price,'min_score':min_score}
			serializer = FiltradoProducto(biblioteca)
			if serializer == 'Bad request':
				if movil == 'true':
					return Response(status=status.HTTP_400_BAD_REQUEST)
				else:
					serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
					return render(request, 'bookalo/index.html', {'productos': serializer.data})
			if movil == 'true':
				return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
			else:
				return render(request, 'bookalo/index.html', {'productos': serializer.data})
		except:
			if movil == 'true':
				return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
			else:
				serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
				return render(request, 'bookalo/index.html', {'productos': serializer.data})


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GetUserProducts(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	token = request.POST.get('token', 'nothing')
	if request.method != 'POST' or token == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
			return render(request, 'bookalo/index.html', {'productos': serializer.data})
	else:
		try:
			serializer = ProductosUsuario(token)
			if movil == 'true':
				return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
			else:
				return render(request, 'bookalo/index.html', {'productos': serializer.data})
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				serializer = ProductoSerializerList(Producto.objects.none(), read_only=True)
				return render(request, 'bookalo/index.html', {'productos': serializer.data})

		

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	token = request.POST.get('token', 'nothing')
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	try:
		files = request.FILES.items()
		latitud = request.POST.get('latitud', '')
		longitud = request.POST.get('longitud', '')
		nombre = request.POST.get('nombre', '')
		precio = request.POST.get('precio', '')
		estado_producto = request.POST.get('estado_producto', '')
		tipo_envio = request.POST.get('tipo_envio', '')
		descripcion = request.POST.get('descripcion', '')
		tags = request.POST.get('tags', '')
		biblioteca = {'files':files,'latitud':latitud,'longitud':longitud,'nombre':nombre,'precio':precio,
									'estado_producto':estado_producto,'tipo_envio':tipo_envio,
									'descripcion':descripcion,'tags':tags,'token':token}
		result = CreacionProducto(biblioteca)
		if movil == 'true':
			if result == 'Created':
				return Response(status=status.HTTP_201_CREATED)
			if result == 'Bad request':
				return Response(status=status.HTTP_400_BAD_REQUEST)
			if result == 'Not found':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if result == 'Created':
				return redirect('/api/get_user_products/')
			else:
				return redirect('/api/generic_product_view')
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			return redirect('/api/generic_product_view')

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateReport(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	token = request.POST.get('token', 'nothing')
	reporteduserUid = request.POST.get('uid', 'nothing')
	comment = request.POST.get('comentario', 'nothing')
	if request.method != 'POST' or token == 'nothing' or reporteduserUid == 'nothing' or comment == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/api/generic_product_view')
	else:
		try:
			CrearReport(reporteduserUid,comment)
			if movil == 'true':
				return Response(status=status.HTTP_201_CREATED)
			else:
				return redirect('/api/get_user_profile')
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return redirect('/api/generic_product_view')
			



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateChat(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	token = request.POST.get('token', 'nothing')
	otroUserUid = request.POST.get('uidUsuario', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST' or token == 'nothing' or otroUserUid == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/api/generic_product_view')
	else:
		try:
			CrearChat(token,otroUserUid,productId)
			if movil == 'true':
				return Response(status=status.HTTP_201_CREATED)
			else:
				return redirect('/api/get_user_profile')
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return redirect('/api/generic_product_view')


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def DeleteProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	token = request.POST.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST' or token == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/api/generic_product_view')
	else:
		try:
			result = BorradoProducto(token,productId)
			if movil == 'true':
				if result == 'Unauthorized':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
					return Response(status=status.HTTP_200_OK)
			else:
				if result == 'Unauthorized':
					return redirect('/api/generic_product_view')
				else:
					return redirect('/api/get_user_products')		
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return redirect('/api/generic_product_view')


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def LikeProduct(request, format=None):
	token = request.POST.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/api/generic_product_view')
	if token == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/api/generic_product_view')
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
