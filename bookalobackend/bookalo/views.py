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
			user_uid = user_info['users'][0]['localId']
			name = user_info['users'][0]['email'].split("@")[0]
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
	return Response()

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