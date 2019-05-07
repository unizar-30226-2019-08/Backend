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


def index(request):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', 0)
	nelements = request.POST.get('elementos_pagina', -1)
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')

	try:
		serializer = GenericProducts(token,last_index,nelements)
		if movil == 'true':
			return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
		else:
			if check_user_logged_in(token):
				user = get_user(token)
				serializer_favs = ProductosFavoritos(token,last_index,nelements)
				return render(request, 'bookalo/index.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 'productos_favoritos':serializer_favs.data, 'productos': serializer.data})
			else:
				return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': serializer.data})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if check_user_logged_in(token):
				user = get_user(token)
				return render(request, 'bookalo/index.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 'productos_favoritos':serializer_favs.data, 'productos': serializer.data})
			else:
				return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': serializer.data})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def Login(request, format=None):
	token = request.POST.get('token', 'nothing')
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'error' : 'Token no recibido.'})
	else:
		retorno = usuario_login(token)
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
					return render(request, 'bookalo/productodetallado.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 'productos_favoritos':serializer_favs.data,  'producto': serializer.data})
				else:
					return render(request, 'bookalo/productodetallado.html', {'loggedin': False,'producto': serializer.data})
		else:
			if movil == 'true':
				return Response({'producto': serializer.data}, status=status.HTTP_200_OK)
			else:
				if check_user_logged_in(token):
					serializer_favs = ProductosFavoritos(token,0,-1)
					user = get_user(token)
					return render(request, 'bookalo/productodetallado.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 'productos_favoritos':serializer_favs.data,  'producto': serializer.data})
				else:
					return render(request, 'bookalo/productodetallado.html', {'loggedin': False, 'producto': serializer.data})
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			if check_user_logged_in(token):
				serializer_favs = ProductosFavoritos(token,0,-1)
				user = get_user(token)
				return render(request, 'bookalo/productodetallado.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(user).data, 'productos_favoritos':serializer_favs.data,  'producto': 'exception_in_server'})
			else:
				return render(request, 'bookalo/productodetallado.html', {'loggedin': False,'producto': 'exception_in_server'})


@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetUserProfile(request, format=None):
	token = request.session.get('token', 'nothing')		# Se extrae de la sesión el token
	user_uid = request.GET.get('uid', 'nothing')		# Se coge de las cookies el uid

	if token == 'nothing' and user_uid == 'nothing':
		# Se retorna a usuario a la pagina anterior
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': False, 'error' : 'El usuario no se ha encontrado y no hay sesión iniciada.'})
	elif token != 'nothing' and user_uid == 'nothing':
		if check_user_logged_in(token):
			try:
				fetch_user = get_user(token)
				return render(request, 'bookalo/perfilusuario.html', {'loggedin': True, 'informacion_basica' : UserProfileSerializer(fetch_user).data, 
					'productos_favoritos':ProductosFavoritos(token,0,-1).data, 'productos' : ProductosFavoritos(token,0,-1).data, 
					'valoraciones': usuario_getvaloraciones(fetch_user.uid), 'coincidentUser': True })
			except:
				print("Except")
				return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': False, 'error' : 'El usuario no ha sido encontrado.'})
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': False, 'error' : 'El usuario no tiene sesión iniciada.'})
	elif token == 'nothing' and user_uid != 'nothing':
		fetch_user2 = GetOtherUserProfile(user_uid)
		logged_in = check_user_logged_in(token)
		if fetch_user2 == None:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged_in, 'error' : 'El usuario no ha sido encontrado.'})
		else:
			products = Producto.objects.filter(vendido_por=fetch_user2)	
			serializer = ProductoSerializerList(products, many=True, read_only=True)
			return render(request, 'bookalo/perfilusuario.html', {'loggedin': logged_in, 'informacion_basica' : UserProfileSerializer(fetch_user2).data, 
				'productos' : serializer.data, 'valoraciones': usuario_getvaloraciones(fetch_user2.uid), 'coincidentUser': False})
	else:
		fetch_user2 = GetOtherUserProfile(user_uid)
		logged_in = check_user_logged_in(token)
		if fetch_user2 == None:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged_in, 'error' : 'El usuario no ha sido encontrado.'})
		else:
			products = Producto.objects.filter(vendido_por=fetch_user2)	
			serializer = ProductoSerializerList(products, many=True, read_only=True)
			serializer_favs = ProductosFavoritos(token,0,-1)
			return render(request, 'bookalo/perfilusuario.html', {'loggedin': logged_in, 'informacion_basica' : UserProfileSerializer(fetch_user2).data , 
				'productos_favoritos':serializer_favs.data, 'productos' : serializer.data , 'valoraciones': usuario_getvaloraciones(user_uid), 
				'coincidentUser': False})


@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def FilterProduct(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', 0)
	nelements = request.POST.get('elementos_pagina', -1)
	if request.method != 'POST':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': []})
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': []})
	else:
		logged = check_user_logged_in(token)
		try:
			tags = request.POST.get('tags', -1)
			user_latitude = request.POST.get('latitud', -1)
			user_longitude = request.POST.get('longitud', -1)
			max_distance = request.POST.get('distancia_maxima', -1)
			min_price = request.POST.get('precio_minimo', -1)
			max_price = request.POST.get('precio_maximo', -1)
			min_score = request.POST.get('calificacion_minima', -1)
			search = request.POST.get('busqueda', -1)
			if movil != 'true':
				if min_price != "":
					min_price, max_price = min_price.split(',')
				else:
					min_price = -1
					max_price = -1
			biblioteca = {'tags':tags, 'user_latitude':user_latitude, 'user_longitude':user_longitude, 'max_distance':max_distance,
						'min_price':min_price,'max_price':max_price,'min_score':min_score, 'busqueda' : search}
			
			serializer = FiltradoProducto(biblioteca,token,last_index,nelements)

			if logged:
				user = get_user(token)
				if serializer == 'Bad request':
					if movil == 'true':
						return Response(status=status.HTTP_400_BAD_REQUEST)
					else:
						serializer_favs = ProductosFavoritos(token,last_index,nelements)
						return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data,  'productos': []})
				if movil == 'true':
					return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
				else:
					return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data, 'productos': serializer.data})
			else:
				if serializer == 'Bad request':
					if movil == 'true':
						return Response(status=status.HTTP_400_BAD_REQUEST)
					else:
						return render(request, 'bookalo/index.html', {'loggedin': False, 'productos': []})
				if movil == 'true':
					return Response({'productos': serializer.data}, status=status.HTTP_200_OK)
				else:
					return render(request, 'bookalo/index.html', {'loggedin': False,'productos': serializer.data})
		except:
			if movil == 'true':
				return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
			else:
				if logged:
					serializer_favs = ProductosFavoritos(token,last_index,nelements)
					return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 
						'productos_favoritos':serializer_favs.data, 'productos': []})
				else:
					return render(request, 'bookalo/index.html', {'loggedin': logged, 'productos': []})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetUserProducts(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	last_index = request.POST.get('ultimo_indice', 0)
	nelements = request.POST.get('elementos_pagina', -1)
	user_uid = request.POST.get('uid', 'nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	if token == 'nothing' and movil != 'true':
		return render(request, 'bookalo/index.html', {'loggedin': False, 'productos' : []})
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
					return render(request, 'bookalo/enventa.html', {'loggedin': logged, 
						'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data, 'productos': serializer.data})
				else:
					return render(request, 'bookalo/enventa.html', {'loggedin': logged, 'productos': serializer.data})

		except:
			if movil == 'true':
				return Response(status=status.HTTP_404_NOT_FOUND)
			else:
				if logged:
					serializer_favs = ProductosFavoritos(token,last_index,nelements)
					return render(request, 'bookalo/index.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data, 'productos': []})
				else:
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
		latitud = request.POST.get('latitud', '15')
		longitud = request.POST.get('longitud', '15')
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
				return redirect('/api/get_user_products')
			else:
				return redirect('/')
	except:
		if movil == 'true':
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		else:
			return redirect('/')

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def CreateReport(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')

	reporteduserUid = request.POST.get('uid', 'nothing')
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
				CrearReport(reporteduserUid, cause, comment)
				if movil == 'true':
					return Response(status=status.HTTP_201_CREATED)
				else:
					user = get_user(token)
					serializer_favs = ProductosFavoritos(token,0,-1)
					return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'), {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos': serializer_favs.data, 'info':'OK'})
			else:
				if movil == 'true':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
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
	movil = request.META.get('HTTP_APPMOVIL','nothing')
	if movil == 'true':
		token = request.POST.get('token', 'nothing')
	else:
		token = request.session.get('token', 'nothing')
	productId = request.POST.get('idProducto', 'nothing')
	if request.method != 'POST' or token == 'nothing' or productId == 'nothing':
		if movil == 'true':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			return redirect('/')
	else:
		try:
			check_user_logged_in(token)
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
				return redirect('/')

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
					return HttpResponseRedirect('bookalo/chat.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos': serializer_favs.data, 'chat_cargado': str(chat.pk)})
			else:
				if movil == 'true':
					return Response(status=status.HTTP_401_UNAUTHORIZED)
				else:
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
		if message_created:
			return Response(status=status.HTTP_200_OK)	
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)	
	else:
		return Response(status=status.HTTP_401_UNAUTHORIZED)

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetMessages(request, format=None):
	movil = request.META.get('HTTP_APPMOVIL','nothing')
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
		messages = GetUserMessages(chat_id, user)
		if messages != None:
			return Response({'mensajes':messages}, status=status.HTTP_200_OK)	
		else:
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
			return Response({'chat_vendedor': serializer_chats_vendedor.data, 'chat_comprador':serializer_chats_comprador.data}, 
				status=status.HTTP_200_OK)
		else:
			serializer_favs = ProductosFavoritos(token,last_index,nelements)
			return render(request, 'bookalo/chat.html', {'chat_vendedor': serializer_chats_vendedor.data, 'chat_comprador':serializer_chats_comprador.data, 
				'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos': serializer_favs.data})
	else:
		if movil == 'true':
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		else:
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
		stars = int(stars)
		if movil != 'true':
			stars = stars * 2
		rated_user_id = request.POST.get('uid_usuario_valorado', 'nothing')
		comment = request.POST.get('comentario', '')
		product_id = request.POST.get('id_producto_valorado', 'nothing')
		has_been_rated = ValorarVenta(token, rated_user_id, comment, product_id, stars)
		if has_been_rated:
			return Response(status=status.HTTP_200_OK)
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)	
	else:
		if movil == 'true':
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		else:
			return render(request, 'bookalo/chat.html', {'loggedin': logged})
@api_view(('POST', 'GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def GetRatings(request, format=None):
	token = request.POST.get('token', 'nothing')
	user_uid = request.POST.get('uid', 'nothing')
	if user_uid == 'nothing':
		if token == 'nothing':
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			user = get_user(token)
			user_uid = user.uid
	serializer = usuario_getvaloraciones(user_uid)
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
def PrivacyPolicy(request, format=None):
	token = request.session.get('token', 'nothing')
	if token == 'nothing':
		logged = False
	else:
		logged = check_user_logged_in(token)
	if logged:
		user = get_user(token)
	return render(request, 'bookalo/privacypolicy.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data})

@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def CreateProductRender(request, format=None):
	token = request.session.get('token', 'nothing')
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
		print(logged)
		return render(request, 'bookalo/nuevoproducto.html', {'loggedin': logged, 'informacion_basica' : UserProfileSerializer(user).data , 'productos_favoritos':serializer_favs.data,'productos': [], 'tags':serialized_tags})
	else:
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
				return Response({'notifiaciones': result}, status=status.HTTP_200_OK)
			else:
				return Response(status=status.HTTP_404_NOT_FOUND)
		except:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#Funcion especifica para web para gestionar el logout
@api_view(('POST','GET'))
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def Logout(request, format=None):
	request.session.pop('token')
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
