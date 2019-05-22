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
from .funciones_usuario import *
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import itertools
from django.urls import reverse
import urllib.request
import json
import textwrap

from .middleware import process_request

def index(request):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		last_index = request.POST.get('ultimo_indice', '0')
		nelements = request.POST.get('elementos_pagina', '-1')
	else:
		last_index = request.GET.get('ultimo_indice', '0')
		nelements = request.GET.get('elementos_pagina', '6')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	try:
		serializer, tope = GenericProducts(token,last_index,nelements)
		if movil == 'true':
			return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
		else:
			if check_user_logged_in(token):
				user = get_user(token)
				serializer_favs = ProductosFavoritos(token,last_index,nelements)
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				if int(last_index) - int(nelements) < 0:
					ultimo_indice_anterior = 0
				else:
					ultimo_indice_anterior = int(last_index) - int(nelements)
				return render(request, 'bookalo/index.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 
					'productos_favoritos':serializer_favs.data, 'productos': serializer.data, 'tiene_notificaciones':tiene_notificaciones,
					'ultimo_indice_anterior':ultimo_indice_anterior, 'ultimo_indice_siguiente':int(last_index)+int(nelements), 'tope':tope})
			else:
				if 'token' in request.session:
						request.session.pop('token')
				if int(last_index) - int(nelements) < 0:
					ultimo_indice_anterior = 0
				else:
					ultimo_indice_anterior = int(last_index) - int(nelements)
				return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': serializer.data,
					'ultimo_indice_anterior':ultimo_indice_anterior, 'ultimo_indice_siguiente':int(last_index)+int(nelements), 'tope':tope})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if check_user_logged_in(token):
				user = get_user(token)
				serializer_favs = ProductosFavoritos(token,last_index,nelements)
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				if int(last_index) - int(nelements) < 0:
					ultimo_indice_anterior = 0
				else:
					ultimo_indice_anterior = int(last_index) - int(nelements)
				return render(request, 'bookalo/index.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 
					'productos_favoritos':serializer_favs.data, 'productos': [], 'tiene_notificaciones':tiene_notificaciones,
					'ultimo_indice_anterior':ultimo_indice_anterior, 'ultimo_indice_siguiente':int(last_index)+int(nelements)})
			else:
				if 'token' in request.session:
						request.session.pop('token')
				if int(last_index) - int(nelements) < 0:
					ultimo_indice_anterior = 0
				else:
					ultimo_indice_anterior = int(last_index) - int(nelements)
				return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': [],
					'ultimo_indice_anterior':ultimo_indice_anterior, 'ultimo_indice_siguiente':int(last_index)+int(nelements)})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def Login(request, format=None):
	token = request.POST.get('token', 'nothing')
	fcm_token = request.POST.get('fcm_token', 'nothing')
	print(fcm_token)
	latitude = request.POST.get('latitud', '-1')
	longitude = request.POST.get('longitud', '-1')
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil != 'true':
		fcm_type = 'web'
	else:
		fcm_type = 'android'
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'error' : 'Token no recibido.'})
	else:
		retorno = usuario_login(token, fcm_token, latitude, longitude, fcm_type, movil)
		if retorno == 'Error':
			if movil != 'true':
				return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'error' : 'El usuario no existe.'})
			else:
				return Response(status=status.HTTP_404_NOT_FOUND)
		else:
			if retorno == status.HTTP_401_UNAUTHORIZED:
				if movil != 'true':
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'error' : 'El usuario esta baneado.'})
				else:
					return Response(retorno, status=status.HTTP_401_UNAUTHORIZED)
			else:
				if movil != 'true':
					request.session['token'] = token
					request.session['token_fcm'] = fcm_token
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), retorno)
				else:
					return Response(retorno, status=status.HTTP_200_OK)

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GenericProductView(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	product_pk = request.GET.get('id', 'nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	try:
		serializer = GetProduct(product_pk,token)
		if serializer == 'NOT FOUND':
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				if check_user_logged_in(token):
					serializer_favs = ProductosFavoritos(token,0,-1)
					user = get_user(token)
					notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
					tiene_notificaciones = notifications > 0
					return render(request, 'bookalo/productodetallado.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data,
					 'productos_favoritos':serializer_favs.data,  'producto': serializer.data, 'tiene_notificaciones':tiene_notificaciones})
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return render(request, 'bookalo/productodetallado.html', {'loggedin': False,'producto': serializer.data})
		else:
			if movil == 'true':
				return Response({'producto': serializer.data}, status=status.HTTP_200_OK)
			else:
				if check_user_logged_in(token):
					serializer_favs = ProductosFavoritos(token,0,-1)
					user = get_user(token)
					notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
					tiene_notificaciones = notifications > 0
					return render(request, 'bookalo/productodetallado.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 
						'productos_favoritos':serializer_favs.data,  'producto': serializer.data, 'tiene_notificaciones':tiene_notificaciones})
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return render(request, 'bookalo/productodetallado.html', {'loggedin': False, 'producto': serializer.data})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if check_user_logged_in(token):
				serializer_favs = ProductosFavoritos(token,0,-1)
				user = get_user(token)
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/productodetallado.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data,
				 'productos_favoritos':serializer_favs.data,  'producto': 'exception_in_server', 'tiene_notificaciones':tiene_notificaciones})
			else:
				if 'token' in request.session:
						request.session.pop('token')
				return render(request, 'bookalo/productodetallado.html', {'loggedin': False,'producto': 'exception_in_server'})


@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetUserProfile(request, format=None):
	token = request.session.get('token', 'nothing')		# Se extrae de la sesión el token
	user_uid = request.GET.get('uid', 'nothing')		# Se coge de las cookies el uid

	if token == 'nothing' and user_uid == 'nothing':
		# Se retorna a usuario a la pagina anterior
		return redirect('/')
		#return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': False, 'error' : 'El usuario no se ha encontrado y no hay sesión iniciada.'})
	elif token != 'nothing' and user_uid == 'nothing':
		if check_user_logged_in(token):
			try:
				fetch_user = get_user(token)
				try:
					notif = NotificacionesPendientes.objects.filter(usuario_pendiente=fetch_user)
					notif_serializer = NotificationSerializer(notif, many=True).data
				except:
					notif_serializer = []
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=fetch_user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/perfilusuario.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(fetch_user).data, 
					'productos_favoritos':ProductosFavoritos(token,0,-1).data, 'productos' : ProductosFavoritos(token,0,-1).data, 
					'notificaciones':notif_serializer, 'valoraciones': usuario_getvaloraciones(fetch_user.uid,-1,-1), 'coincidentUser': True , 'tiene_notificaciones':tiene_notificaciones})
			except:
				return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': False, 'error' : 'El usuario no ha sido encontrado.'})
		else:
			if 'token' in request.session:
				request.session.pop('token')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': False, 'error' : 'El usuario no tiene sesión iniciada.'})
	elif token == 'nothing' and user_uid != 'nothing':
		fetch_user2 = GetOtherUserProfile(user_uid)
		logged_in = check_user_logged_in(token)
		if fetch_user2 == None:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged_in, 'error' : 'El usuario no ha sido encontrado.'})
		else:
			products = Producto.objects.filter(vendido_por=fetch_user2)	
			serializer = ProductoSerializerList(products, many=True, read_only=True)
			return render(request, 'bookalo/perfilusuario.html', {'loggedin': logged_in, 'otro_usuario' : UserProfileSerializer(fetch_user2).data, 
				'productos' : serializer.data, 'valoraciones': usuario_getvaloraciones(fetch_user2.uid,-1,-1), 'coincidentUser': False})
	else:
		fetch_user2 = GetOtherUserProfile(user_uid)
		logged_in = check_user_logged_in(token)
		if fetch_user2 == None:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged_in, 'error' : 'El usuario no ha sido encontrado.'})
		else:
			products = Producto.objects.filter(vendido_por=fetch_user2)
			if logged_in:
				user = get_user(token)
				serializer = ProductoSerializerList(products, many=True, read_only=True, context = {"user": user})
				serializer_favs = ProductosFavoritos(token,0,-1)
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/perfilusuario.html', {'loggedin': logged_in, 'informacion_basica' : UserProfileSerializer(user).data , 
					'productos_favoritos':serializer_favs.data, 'productos' : serializer.data , 'valoraciones': usuario_getvaloraciones(user_uid,-1,-1), 
					'otro_usuario': UserProfileSerializer(fetch_user2).data,'coincidentUser': False, 'tiene_notificaciones':tiene_notificaciones})
			else:
				serializer = ProductoSerializerList(products, many=True, read_only=True)
				if 'token' in request.session:
					request.session.pop('token')
				return render(request, 'bookalo/perfilusuario.html', {'loggedin': logged_in, 'productos' : serializer.data , 
					'valoraciones': usuario_getvaloraciones(user_uid,-1,-1), 'otro_usuario': UserProfileSerializer(fetch_user2).data,
					'coincidentUser': False})



@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def FilterProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', '0')
	nelements = request.POST.get('elementos_pagina', '-1')
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
			#return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': []})
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	#if token == 'nothing':
	#	if movil == 'true':
	#		return Response(status=status.HTTP_400_BAD_REQUEST)
	#	else:
	#		#return redirect('/')
	#		return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': []})
	#else:
	logged = check_user_logged_in(token)
	try:
		tags = request.POST.get('tags', '-1')
		if tags == '':
			tags = '-1'
		user_latitude = request.POST.get('latitud', '-1')
		if user_latitude == '':
			user_latitude = '-1'
		user_longitude = request.POST.get('longitud', '-1')
		if user_longitude == '':
			user_longitude == '-1'
		max_distance = request.POST.get('distancia_maxima', '-1')
		if max_distance == '':
			max_distance = '-1'
		min_price = request.POST.get('precio_minimo', '-1')
		if min_price == '':
			min_price = '-1'
		max_price = request.POST.get('precio_maximo', '-1')
		if max_price == '':
			max_price = '-1'
		min_score = request.POST.get('calificacion_minima', '-1')
		if min_score == '':
			min_score = '-1'
		search = request.POST.get('busqueda', '-1')
		if search == '':
			search = '-1'
		if movil != 'true':
			if min_price != '-1':
				min_price, max_price = min_price.split(',')
			else:
				#min_price = '-1'
				max_price = '-1'
		print(user_latitude)
		print(user_longitude)
		biblioteca = {'tags':tags, 'user_latitude':user_latitude, 'user_longitude':user_longitude, 'max_distance':max_distance,
					'min_price':min_price,'max_price':max_price,'min_score':min_score, 'busqueda' : search}
		
		serializer = FiltradoProducto(biblioteca,token,last_index,nelements)

		if logged:
			user = get_user(token)
			if serializer == 'Bad request':
				if movil == 'true':
					return Response(status=status.HTTP_400_BAD_REQUEST)
				else:
					return redirect('/')
			if movil == 'true':
				return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
			else:
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data ,
				 'productos_favoritos':ProductosFavoritos(token,0,-1).data, 'productos': serializer.data, 'tiene_notificaciones':tiene_notificaciones,
				 'filter_product':True})
		else:
			if serializer == 'Bad request':
				if movil == 'true':
					return Response(status=status.HTTP_400_BAD_REQUEST)
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return redirect('/')
					#return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': []})
			if movil == 'true':
				return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
			else:
				if 'token' in request.session:
					request.session.pop('token')
				return render(request, 'bookalo/index.html', {'loggedin': False,'productos': serializer.data, 'filter_product':True})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if logged:
				user = get_user(token)
				serializer_favs = ProductosFavoritos(token,last_index,nelements)
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
					'productos_favoritos':serializer_favs.data, 'productos': [], 'tiene_notificaciones':tiene_notificaciones, 'filter_product':True})
			else:
				if 'token' in request.session:
					request.session.pop('token')
				return render(request, 'bookalo/index.html', {'loggedin': logged, 'productos': [], 'filter_product':True})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetUserProducts(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', 'nothing')
	if last_index == 'nothing':
		last_index = 0
	else:
		last_index = int(last_index)
	nelements = request.POST.get('elementos_pagina', 'nothing')
	if nelements == 'nothing':
		nelements = -1
	else:
		nelements = int(nelements)
	user_uid = request.POST.get('uid', 'nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing' and movil != 'true':
		#return render(request, 'bookalo/index.html', {'loggedin': False, 'productos' : []})
		return redirect('/')
	else:
		logged = check_user_logged_in(token)
		user = get_user(token)

		try:
			if movil == 'true' and token == 'nothing' and user_uid == 'nothing':
				return Response(status=status.HTTP_400_BAD_REQUEST)
			serializer = ProductosUsuario(token, last_index, nelements, user_uid)
			
			if movil == 'true':
				return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
			else:
				if logged:
					serializer_favs = ProductosFavoritos(token,last_index,nelements)
					notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
					tiene_notificaciones = notifications > 0
					return render(request, 'bookalo/enventa.html', {'loggedin': logged, 
						'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data, 
						'productos': serializer.data, 'tiene_notificaciones':tiene_notificaciones})
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return render(request, 'bookalo/enventa.html', {'loggedin': logged, 'productos': serializer.data})

		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				if logged:
					serializer_favs = ProductosFavoritos(token,last_index,nelements)
					notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
					tiene_notificaciones = notifications > 0
					return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data ,
					 'productos_favoritos':serializer_favs.data, 'productos': [], 'tiene_notificaciones':tiene_notificaciones})
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return render(request, 'bookalo/index.html', {'loggedin': logged, 'productos': []})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def CreateProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return render(request, 'bookalo/nuevoproducto.html', {'loggedin': False, 'error' : 'La peticion es incorrecta'})
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return render(request, 'bookalo/index.html', {'loggedin': False})
	try:
		logged = check_user_logged_in(token)
		files = request.FILES.getlist('files')
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
		print(biblioteca)
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
				return redirect('/api/get_user_products')
			else:
				return redirect('/')
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if 'token' in request.session:
				request.session.pop('token')
			return redirect('/')

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def CreateReport(request, format=None):
	print("A crear")
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')

	reporteduserUid = request.POST.get('uid', 'nothing')
	print(reporteduserUid)
	cause = request.POST.get('causa', 'nothing')
	comment = request.POST.get('comentario', 'nothing')
	if request.method != 'POST' or token == 'nothing' or reporteduserUid == 'nothing' or comment == 'nothing' or cause == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
	else:
		try:
			logged = check_user_logged_in(token)
			if logged:
				print("Voy a crear")
				CrearReport(reporteduserUid, cause, comment)
				if movil == 'true':
					return Response(status=status.HTTP_201_CREATED)
				else:
					user = get_user(token)
					serializer_favs = ProductosFavoritos(token,0,-1)
					notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
					tiene_notificaciones = notifications > 0
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
						'productos_favoritos': serializer_favs.data, 'info':'OK', 'tiene_notificaciones':tiene_notificaciones})
			else:
				if movil == 'true':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'error':'El usuario no tiene sesión iniciada'})
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return redirect('/')

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def DeleteProduct(request, format=None):
	print('HEY')
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	print(productId)
	if request.method != 'POST' or token == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
	else:
		try:
			if check_user_logged_in(token):
				result = BorradoProducto(token,productId)
				if movil == 'true':
					if result == 'Unauthorized':
						return Response(status=status.HTTP_401_UNAUTHORIZED)
					else:
						return Response(status=status.HTTP_200_OK)
				else:
					if result == 'Unauthorized':
						return redirect('/')
					else:
						return redirect('/api/get_user_products')
			else:
				if movil == 'true':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return redirect('/')
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return redirect('/')

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def LikeProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
	if token == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
	else:
		try:
			result = LikeProducto(token, productId)
			if result == 'OK':
				if movil == 'true':
					return Response(status=status.HTTP_200_OK)
				else:
					return redirect('/api/get_user_profile')
			else:
				if movil == 'true':
					return Response(status=status.HTTP_404_NOT_FOUND)
				else:
					return redirect('/')
		except:
			if movil == 'true':
					return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				if 'token' in request.session:
					request.session.pop('token')
				return redirect('/')

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetLikedProducts(request, format=None):
	token = request.POST.get('token', '')
	last_index = request.POST.get('ultimo_indice', '')
	if last_index == '':
		last_index = 0
	else:
		last_index = int(last_index)
	nelements = request.POST.get('elementos_pagina', '')
	if nelements == '':
		nelements = -1
	else:
		nelements = int(nelements)
	if token == '':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			serializer_favs = ProductosFavoritos(token, last_index, nelements)
			return Response({'productos_favoritos':serializer_favs.data}, status=status.HTTP_200_OK)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def CreateChat(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')

	otroUserUid = request.POST.get('uidUsuario', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST' or token == 'nothing' or otroUserUid == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
	else:
		try:
			logged = check_user_logged_in(token)
			if logged:
				chat = CrearChat(token, otroUserUid, productId)
				if movil == 'true':
					return Response({'chat_cargado': ChatSerializer(chat).data}, status=status.HTTP_201_CREATED)
				else:
					user = get_user(token)
					serializer_favs = ProductosFavoritos(token,0,-1)
					notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
					tiene_notificaciones = notifications > 0
					return render(request,'bookalo/chat.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
						'productos_favoritos': serializer_favs.data, 'chat_cargado': str(chat.pk), 'tiene_notificaciones':tiene_notificaciones})
			else:
				if movil == 'true':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
					if 'token' in request.session:
						request.session.pop('token')
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'error':'El usuario no tiene sesión iniciada'})
		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				return redirect('/')

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def SendMessage(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		message = request.POST.get('mensaje', '')
		chat_id = request.POST.get('id_chat', '')
		message_created = CrearMensaje(token, chat_id, message)
		try:
			user = get_user(token)
			chat = Chat.objects.get(pk=int(chat_id))
			if chat.vendedor == user:
				soy_vendedor = True
				user_recibe = chat.comprador
			else:
				soy_vendedor = False
				user_recibe = chat.vendedor
		except:
			message_created = None
		if message_created != None:
			if SendFCMMessage(chat_id, message_created, token, user, soy_vendedor, user_recibe):
				return Response(status=status.HTTP_200_OK)
			else:
				return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)	
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)	
	else:
		return Response(status=status.HTTP_401_UNAUTHORIZED)

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetMessages(request, format=None):
	print("Getting")
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', 0)
	nelements = request.POST.get('elementos_pagina', -1)
	if movil == 'true':
		token = request.POST.get('token', '')
	else:
		#Comprobar que se puede coger el token de las cookies aunque se haga petición mediante JS
		token = request.session.get('token', '')
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		chat_id = request.POST.get('id_chat', '')
		if chat_id == '' or token == '':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		user = get_user(token)
		messages = GetUserMessages(chat_id, user,last_index,nelements)
		print(messages)
		if messages != None:
			if movil == 'true':
				return Response({'mensajes':messages.data}, status=status.HTTP_200_OK)
			else:
				try:
					info_messages = GetChatInfoWeb(chat_id)
					return Response({'mensajes':messages.data, 'vendedor': info_messages['vendedor'], 'comprador': info_messages['comprador'], 'producto':info_messages['producto']}, status=status.HTTP_200_OK)
				except:
					return Response({'mensajes':messages.data}, status=status.HTTP_200_OK)	
		else:
			print("404")
			return Response(status=status.HTTP_404_NOT_FOUND)	
	else:
		return Response(status=status.HTTP_401_UNAUTHORIZED)

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetChats(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', 0)
	nelements = request.POST.get('elementos_pagina', -1)
	what_chats = request.POST.get('tipo_chats', '')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		user = get_user(token)
		serializer_chats_vendedor = GetChatVendedor(user,last_index,nelements)
		serializer_chats_comprador = GetChatComprador(user,last_index,nelements)
		if movil == 'true':
			if what_chats == 'compra':
				return Response({'chats':serializer_chats_comprador.data}, status=status.HTTP_200_OK)
			elif what_chats == 'venta':
				return Response({'chats': serializer_chats_vendedor.data}, status=status.HTTP_200_OK)
			else:
				return Response({'chat_vendedor': serializer_chats_vendedor.data, 'chat_comprador':serializer_chats_comprador.data}, status=status.HTTP_200_OK)
		else:
			serializer_favs = ProductosFavoritos(token,last_index,nelements)
			notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
			tiene_notificaciones = notifications > 0
			return render(request, 'bookalo/chat.html', {'chat_vendedor': serializer_chats_vendedor.data, 'chat_comprador':serializer_chats_comprador.data, 
				'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones})
	else:
		if movil == 'true':
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		else:
			if 'token' in request.session:
				request.session.pop('token')
			return render(request, 'bookalo/chat.html', {'loggedin': logged})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def SendRating(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		stars = request.POST.get('estrellas', 'nothing')
		print(stars)
		stars = int(stars)
		if movil != 'true':
			stars = stars * 2
		rated_user_id = request.POST.get('uid_usuario_valorado', 'nothing')
		print(rated_user_id)
		comment = request.POST.get('comentario', '')
		print(comment)
		product_id = request.POST.get('id_producto_valorado', 'nothing')
		print(product_id)
		serializer_favs = ProductosFavoritos(token, 0, -1)
		has_been_rated = ValorarVenta(token, rated_user_id, comment, product_id, stars)
		user = get_user(token)
		if has_been_rated:
			if movil == 'true':
				return Response(status=status.HTTP_200_OK)
			else:
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/chat.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
					'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones})
		else:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
				tiene_notificaciones = notifications > 0
				return render(request, 'bookalo/chat.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
					'productos_favoritos': serializer_favs.data,'error':'La venta no ha podido ser valorada', 'tiene_notificaciones':tiene_notificaciones})
	else:
		if movil == 'true':
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		else:
			if 'token' in request.session:
				request.session.pop('token')
			return render(request, 'bookalo/chat.html', {'loggedin': logged})
			
@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetRatings(request, format=None):
	token = request.POST.get('token', 'nothing')
	user_uid = request.POST.get('uid', 'nothing')
	last_index = request.POST.get('ultimo_indice', 0)
	nelements = request.POST.get('elementos_pagina', -1)
	if user_uid == 'nothing':
		if token == 'nothing':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			user = get_user(token)
			user_uid = user.uid
	serializer = usuario_getvaloraciones(user_uid,last_index,nelements)
	if serializer == None:
		return Response(status=status.HTTP_404_NOT_FOUND)
	else:
		return Response({'valoraciones':serializer}, status=status.HTTP_200_OK)

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetUserInfo(request, format=None):
	token = request.POST.get('token', 'nothing')
	user_uid = request.POST.get('uid', 'nothing')
	if user_uid == 'nothing':
		if token == 'nothing':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			user = get_user(token)
			user_uid = user.uid
	serializer = GetBasicInfo(user_uid)
	if serializer == None:
		return Response(status=status.HTTP_404_NOT_FOUND)
	else:
		return Response({'informacion_basica':serializer}, status=status.HTTP_200_OK)

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetTagList(request, format=None):
	serialized_tags = GetTags('all')
	if serialized_tags != None:
		return Response({'tags':serialized_tags}, status=status.HTTP_200_OK)
	else:
		return Response({'tags':[]}, status=status.HTTP_404_NOT_FOUND)

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def SellProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		user = get_user(token)
		serializer_favs = ProductosFavoritos(token, 0, -1)
		notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
		tiene_notificaciones = notifications > 0
		chat_id = request.POST.get('id_chat', '')
		if chat_id == '' or token == 'nothing':
			if movil == 'true':
				return Response(status=status.HTTP_400_BAD_REQUEST)
			else:
				
				return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
					'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones, 'error':'Es necesario que la peticion tenga el id del producto'})
		else:
			chat_buscado = Chat.objects.get(pk=int(chat_id))
			was_marked = MarkAsSold(chat_buscado.producto.id, token)
			if was_marked == None:
				if movil == 'true':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
						'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones, 'error':'El usuario no esta logeado o no es el dueño del producto'})
			elif was_marked == False:
				if movil == 'true':
					return Response(status=status.HTTP_404_NOT_FOUND)
				else:
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
						'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones, 'error':'El producto no se ha encontrado'})
			else:
				user1 = chat_buscado.vendedor
				user2 = chat_buscado.comprador
				try:
					notificacion1 = NotificacionesPendientes(usuario_pendiente=user1, otro_usuario_compra=user2, producto=chat_buscado.producto, descripcion_notificacion= Mensaje)
					notificacion2 = NotificacionesPendientes(usuario_pendiente=user2, otro_usuario_compra=user1, producto=chat_buscado.producto, descripcion_notificacion= Mensaje)
					notificacion1.save()
					notificacion2.save()
					try:
						mensaje = Mensaje.objects.get(chat_asociado=chat_buscado, es_valoracion=True)
						mensaje.valoracion = None
					except:
						print('Mensaje no existia')
						mensaje = CrearMensaje(token, str(chat_buscado.pk), "Notificacion")

					if mensaje != None:
						mensaje.es_valoracion = True
						mensaje.save()
						soy_vendedor = True
						mensaje = Mensaje.objects.get(chat_asociado=chat_buscado, es_valoracion=True)
						if SendFCMMessage(str(chat_buscado.pk), mensaje, token, user1, soy_vendedor, user2):
							if movil == 'true':
								return Response(status=status.HTTP_200_OK)
							else:
								return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data ,
								 'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones})
						else:
							if movil == 'true':
								return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
							else:
								return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
									'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones, 'error':'Error en las notificaciones'})
					else:
						if movil == 'true':
							return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
						else:
							return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
								'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones, 'error':'Error en las notificaciones'})
				except:
					if movil == 'true':
						return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
					else:
						return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
							'productos_favoritos': serializer_favs.data, 'tiene_notificaciones':tiene_notificaciones, 'error':'Error en las notificaciones'})
				
	else:
		if movil == 'true':
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		else:
			if 'token' in request.session:
				request.session.pop('token')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'error':'El usuario no esta logeado o no se ha pasado el token'})

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def PrivacyPolicy(request, format=None):
	token = request.session.get('token', 'nothing')
	print(token)
	if token == 'nothing':
		return render(request, 'bookalo/privacypolicy.html', {'loggedin': False})
	else:
		logged = check_user_logged_in(token)
		if logged:
			user = get_user(token)
			notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
			tiene_notificaciones = notifications > 0
			return render(request, 'bookalo/privacypolicy.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data, 'tiene_notificaciones':tiene_notificaciones})
		else:
			if 'token' in request.session:
				request.session.pop('token')
			return render(request, 'bookalo/privacypolicy.html', {'loggedin': logged})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def CreateProductRender(request, format=None):
	token = request.session.get('token', 'nothing')
	print(token)
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		serializer_favs = ProductosFavoritos(token ,0 ,-1)
		serialized_tags = GetTags(5)
		if serialized_tags == None:
			serialized_tags = []
		user = get_user(token)
		notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
		tiene_notificaciones = notifications > 0
		print(logged)
		return render(request, 'bookalo/nuevoproducto.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
			'productos_favoritos':serializer_favs.data,'productos': [], 'tags':serialized_tags, 'tiene_notificaciones':tiene_notificaciones})
	else:
		if 'token' in request.session:
			request.session.pop('token')
		return render(request, 'bookalo/nuevoproducto.html', {'loggedin': logged, 'productos': []})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetPendingNotifications(request, format=None):
	token = request.POST.get('token', 'nothing')
	if request.method != 'POST' or token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			result = GetNotifications(token)
			if result != 'NOT FOUND':
				return Response({'notificaciones': result}, status=status.HTTP_200_OK)
			else:
				return Response(status=status.HTTP_404_NOT_FOUND)
		except:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def EditProductRender(request, format=None):
	token = request.session.get('token', 'nothing')
	id_product = request.GET.get('id_producto', 'nothing')
	logged = check_user_logged_in(token)
	if logged:
		serializer_favs = ProductosFavoritos(token ,0 ,-1)
		serialized_tags = GetTags(5)
		if serialized_tags == None:
			serialized_tags = []	
		try:
			user = get_user(token)
			notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid).count()
			tiene_notificaciones = notifications > 0
			product = Producto.objects.get(pk=id_product)
			if product.vendido_por == user:
				return render(request, 'bookalo/edicionproducto.html', {'loggedin': logged, 
					'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data,
					'producto': ProductoSerializer(product).data, 'tags':serialized_tags, 'editando' : True, 'tiene_notificaciones':tiene_notificaciones})
			else:
				return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'error':'El producto no es de ese usuario'})
		except:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'error':'El producto no se ha encontrado'})
	else:
		if 'token' in request.session:
			request.session.pop('token')
		return redirect('/')


@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def EditProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	id_product = request.POST.get('id_producto', 'nothing')
	try:
		logged = check_user_logged_in(token)
		if logged:
			files = request.FILES.getlist('files')
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
			result = EditarProducto(biblioteca,id_product,movil)
			if movil == 'true':
				if result == 'Modified':
					return Response(status=status.HTTP_200_OK)
				if result == 'Bad request':
					return Response(status=status.HTTP_400_BAD_REQUEST)
				if result == 'Not found':
					return Response(status=status.HTTP_404_NOT_FOUND)
				else:
					return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
			else:
				if result == 'Created':
					return redirect('/api/get_user_products')
				else:
					return redirect('/')
		else:
			if movil == 'true':
				return Response(status=status.HTTP_401_UNAUTHORIZED)
			else:
				if 'token' in request.session:
					request.session.pop('token')
				return redirect('/')
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			return redirect('/')


#Funcion especifica para web para gestionar el logout
@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def Logout(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
		token_fcm = request.POST.get('token_fcm', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
		token_fcm = request.session.get('token_fcm', 'nothing')
		if 'token' in request.session:
			request.session.pop('token')
		if 'token_fcm' in request.session:
			request.session.pop('token_fcm')
	if token_fcm != 'nothing':
		try:
			sesiones = Sesion.objects.filter(token_fcm=token_fcm)
			if sesiones:
				for sesion in sesiones:
					sesion.delete()
		except:
			return Response({'error':"Something went wrong while deleting the session"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
	return Response(status=status.HTTP_200_OK)

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def ClearPendingMessages(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	id_chat = request.POST.get('id_chat', 'nothing')
	try:
		user = get_user(token)
		chat = Chat.objects.get(pk=int(id_chat))
		if chat.vendedor == user:
			chat.num_pendientes_vendedor = 0
			chat.save()
			return Response(status=status.HTTP_200_OK)
		elif chat.comprador == user:
			chat.num_pendientes_comprador = 0
			chat.save()
			return Response(status=status.HTTP_200_OK)
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)
	except:
		return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetInfoISBN(request, format=None):
	isbn = request.GET.get('isbn','nothing')
	if isbn == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
	user_input = isbn.strip()
	with urllib.request.urlopen(base_api_link + user_input) as f:
		text = f.read()

	decoded_text = text.decode("utf-8")
	obj = json.loads(decoded_text) # deserializes decoded_text to a Python object
	try:
		volume_info = obj["items"][0] 
		authors = obj["items"][0]["volumeInfo"]["authors"]

		try:
			titulo = volume_info["volumeInfo"]["title"]
		except:
			titulo = 'Titulo no disponible'
		try:
			resumen = textwrap.fill(volume_info["searchInfo"]["textSnippet"])
		except:
			resumen = 'Resumen no disponible'
		try:
			autores = ",".join(authors)
		except:
			autores = 'Autor no disponible'
		try:
			page_count = volume_info["volumeInfo"]["pageCount"]
		except:
			page_count = 'Numero de paginas no disponible'
		try:
			lenguaje = volume_info["volumeInfo"]["language"]
		except:
			lenguaje = 'Lenguaje no disponible'
		try:
			lista_categorias = volume_info["volumeInfo"]["categories"]
			categorias = ""
			for c in lista_categorias:
				categorias = categorias + c
		except:
			categorias = 'Categorias no disponibles'
		try:
			imagen = volume_info["volumeInfo"]["imageLinks"]["thumbnail"]
		except:
			imagen = 'URL de imagen no disponible'

		descripcion = "Resumen/sinopsis: " + resumen + "\nAutor/es: " + autores + "\nPaginas: " + str(page_count) + "\nIdioma: " + lenguaje + "\nCategorias: " + categorias
		data_libro = {
			"Titulo":titulo,
			"Descripcion": descripcion,
			"url_imagen":imagen
		}
		"""
		"Resumen":resumen,
		"Autor/es":autores,
		"Paginas":page_count,
		"Idioma":lenguaje,
		"Categorias":categorias	
		"""
		#return data_libro
		return Response(data_libro, status=status.HTTP_200_OK)

	except:
		return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def MobileRedirect(request, format=None):
	return render(request, 'bookalo/redirect.html')