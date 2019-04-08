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


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GenericProductView(request, format=None):
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	try:
		products = Producto.objects.order_by('-num_likes')
		serializer = ProductoSerializerList(products, many=True, read_only=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
	except:
		return Response(status=status.HTTP_404_NOT_FOUND)
	


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GetUserProfile(request, format=None):
	token = request.META.get('HTTP_TOKEN', 'nothing')
	auth.refresh(token)
	user_uid = request.POST.get('uid', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or user_uid == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		if check_user_logged_in(token):
			try:
				fetch_user = Usuario.objects.get(uid=user_uid)
				return Response(UserProfileSerializer(fetch_user).data, status=status.HTTP_200_OK)
			except:
				return Response(status=status.HTTP_404_NOT_FOUND)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)


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
		return Response(status=status.HTTP_404_NOT_FOUND)
	products = Producto.objects.none()
	for word in search.split():
		if word not in preposiciones:
			productos_palabra = Producto.objects.filter(nombre__contains=word)
			products = products | productos_palabra
	products.distinct()
	serializer = ProductoSerializerList(products, many=True, read_only=True)
	return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def FilterProduct(request, format=None):
	return Response()

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
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)

		user = Usuario.objects.get(uid=user_uid)
		products = Producto.objects.filter(vendido_por=user)
		serializer = ProductoSerializerList(products, many=True, read_only=True)
		return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateProduct(request, format=None):
	return Response()

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
			return Response(ReportSerializer(reporte).data, status=status.HTTP_200_OK)
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
		#NO FUNCIONA TODAVIA
		#try:
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']
			user = Usuario.objects.get(uid=user_uid)
			otroUser = Usuario.objects.get(uid=otroUserUid)
			product = Producto.objects.get(id=productId)
			chat = Chat.objects.create(vendedor=otroUser, comprador=user, producto=product)
			print('hey')
			return Response(ChatSerializer(chat).data, status=status.HTTP_200_OK)
		#except:
		#	return Response(status=status.HTTP_404_NOT_FOUND)	


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
			Producto.objects.get(id=productId).delete()
			return Response(status=status.HTTP_200_OK)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)	
			



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def prueba(request, format=None):
	Comment = request.POST.get('comentario')
	report = Report.objects.create(causa=Comment)
	return Response(ReportSerializer(report).data, status=status.HTTP_200_OK)