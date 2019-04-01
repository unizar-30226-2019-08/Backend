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



@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def Login(request, format=None):
	token = request.POST.get('token', 'nothing')
	if token == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		try:
			user_info = auth.get_account_info(token)
			print(user_info)
			user_uid = user_info['users'][0]['localId']
			print(user_uid)
			name = user_info['users'][0]['email'].split("@")[0]
		except Exception as e:
			print("Hice excepcion not found")
			print(e.message)
			return Response(status=status.HTTP_404_NOT_FOUND)
		
		try:
			print("Estoy en el update")
			user = Usuario.objects.get(uid=user_uid).update(access_token=token)
			return Response(UserSerializer(user).data)

		except Usuario.DoesNotExist:
			print("Estoy en el create")
			new_user_data = Usuario.objects.create(uid=user_uid, access_token=token, nombre=name)
			return Response(UserSerializer(new_user_data).data)

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def GetUser(request, format=None):
	return Response()

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def GetUserProfile(request, format=None):
	return Response()

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