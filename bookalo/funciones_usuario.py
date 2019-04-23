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

def get_user(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		#user = Usuario.objects.get(uid=user_uid).update(ultima_conexion=datetime.now())
		user = Usuario.objects.get(uid=user_uid)
		user.ultima_conexion = datetime.now()
		user.save()
		return user
	except:
		return None

def update_last_connection(user):
	try:
		Usuario.objects.get(uid=user.uid).update(ultima_conexion=datetime.now())
		return True
	except:
		return False

#Comprueba que el usuario este logeado en el sistema
def check_user_logged_in(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		user = Usuario.objects.get(uid=user_uid)#.update(ultima_conexion=datetime.now)
		user.ultima_conexion = datetime.now()
		user.save()
		#auth.refresh(token)
		return True
	except:
		return False

def usuario_login(token):
	
	latitud_registro = 0.0
	longitud_registro = 0.0
	g = GeoIP2()
	
	latitud_registro = 41.683490
	longitud_registro = -0.888479
	
	if token == 'nothing':
		return 'Error'
	else:
		try:
			user_info = auth.get_account_info(token)
			user_uid = user_info['users'][0]['localId']
			try:
				name = user_info['users'][0]['displayName']
				if name == '':
					name = user_info['users'][0]['email'].split("@")[0]
			except:
				name = user_info['users'][0]['email'].split("@")[0]
			try:
				profile_image = user_info['users'][0]['providerUserInfo'][0]['photoUrl']
			except:
				profile_image = 'https://www.iconsdb.com/icons/preview/black/book-xxl.png'
		except:	
			print("Error con firebase en login social")
			return 'Error'
		
		try:
			user = Usuario.objects.get(uid=user_uid)
			user.ultima_conexion = datetime.now()
			user.save(update_fields=['ultima_conexion'])

			if user.esta_baneado:
				return status.HTTP_401_UNAUTHORIZED
			else:
				update_last_connection(user)
				return UserSerializer(user).data

		except Usuario.DoesNotExist:

			new_user_data = Usuario.objects.create(uid=user_uid, nombre=name, latitud_registro=latitud_registro, longitud_registro=longitud_registro, imagen_perfil=profile_image)
			update_last_connection(new_user_data)
			return UserSerializer(new_user_data).data

def usuario_getProfile(token,user_uid):

		#if check_user_logged_in(token):
			#try:
				fetch_user = Usuario.objects.get(uid=user_uid)
				return Response(UserProfileSerializer(fetch_user).data, status=status.HTTP_200_OK)
			#except:
			#	return Response(status=status.HTTP_404_NOT_FOUND)
		#else:
		#	return Response(status=status.HTTP_401_UNAUTHORIZED)


