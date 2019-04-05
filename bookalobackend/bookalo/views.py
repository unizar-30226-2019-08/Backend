from django.shortcuts import render, redirect
from bookalo.pyrebase_settings import db, auth
from bookalo.models import *
from bookalo.serializers import *
#from bookalo.functions import *
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from operator import itemgetter
from django.http import HttpResponse
from datetime import datetime, timedelta, timezone
from django.db.models import Q

#Comprueba que el usuario este logeado en el sistema
def check_user_logged_in(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		user = Usuario.objects.get(uid=user_uid)
		return True
	except:
		return False


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def Login(request, format=None):
	token = request.META.get('HTTP_TOKEN', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user_info = auth.get_account_info(token)
			print(token)
			user_uid = user_info['users'][0]['localId']
			print(user_uid)
			name = user_info['users'][0]['email'].split("@")[0]
			print(name)
		except:
			return Response(status=status.HTTP_404_NOT_FOUND)
		
		try:
			user = Usuario.objects.get(uid=user_uid)
			if user.esta_baneado:
				return Response(UserSerializer(user).data, status=status.HTTP_401_UNAUTHORIZED)
			else:
				return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

		except Usuario.DoesNotExist:
			new_user_data = Usuario.objects.create(uid=user_uid, nombre=name)
			return Response(UserSerializer(new_user_data).data, status=status.HTTP_201_CREATED)

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
	#try:
	#Producto.objects.create(usuario_reportado=reporteduser_uid, causa=Comment)
	preposiciones = ['a','ante','bajo','cabe','con','contra','de','desde','en','entre',
	'hacia','hasta','para','por','segun','sin','so','sobre','tras']
	#products = Producto.objects.filter(nombre="Hola").distinct()
	search = request.POST.get('busqueda')
	products = Q()
	for word in search.split():
		if word not in preposiciones:
			products &= Q(Producto_nombre__icontains=word)
	return Response(UserProfileSerializer(products).data, status=status.HTTP_200_OK, many=True)
	#except:
	#	return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def FilterProduct(request, format=None):
	return Response()

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GetUserProducts(request, format=None):
	return Response()

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateProduct(request, format=None):
	return Response()

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def CreateReport(request, format=None):
	token = request.META.get('HTTP_TOKEN', 'nothing')
	#auth.refresh(token)
	reporteduser_uid = request.POST.get('uid', 'nothing')
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or reporteduser_uid == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		if check_user_logged_in(token):
			try:
				Comment = request.POST.get('comentario')
				report = Report.objects.create(usuario_reportado=reporteduser_uid, causa=Comment)
				return Response(ReportSerializer(report).data, status=status.HTTP_200_OK)
			except:
				return Response(status=status.HTTP_404_NOT_FOUND)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def prueba(request, format=None):
	Comment = request.POST.get('comentario')
	report = Report.objects.create(causa=Comment)
	return Response(ReportSerializer(report).data, status=status.HTTP_200_OK)