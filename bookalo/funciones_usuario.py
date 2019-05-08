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
from django.utils.timezone import now as timezone_now
#from geopy import Nominatim

def get_user(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		user = Usuario.objects.get(uid=user_uid)
		user.ultima_conexion = timezone_now()
		user.save()
		return user
	except:
		return None

def update_last_connection(user):
	try:
		Usuario.objects.get(uid=user.uid).update(ultima_conexion=timezone_now())
		return True
	except:
		return False

#Comprueba que el usuario este logeado en el sistema
def check_user_logged_in(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		user = Usuario.objects.get(uid=user_uid)
		user.ultima_conexion = timezone_now()
		user.save()
		#auth.refresh(token)
		return True
	except:
		return False

def usuario_login(token, token_fcm):

	latitud_registro = 0.0
	longitud_registro = 0.0
	
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
			#geolocator = Nominatim(user_agent="bookalo")
			#location = geolocator.reverse(str(user.latitud_registro) + ',' + str(user.longitud_registro))
			#try:
			#	return location.raw['address']['city']
			#except:
			#	return location.raw['address']['county']
			if user.esta_baneado:
				return status.HTTP_401_UNAUTHORIZED
			else:
				user.token_fcm = token_fcm
				user.save()
				update_last_connection(user)
				return UserSerializer(user).data

		except Usuario.DoesNotExist:

			new_user_data = Usuario.objects.create(username=user_uid, uid=user_uid, token_fcm=token_fcm, nombre=name, latitud_registro=latitud_registro, longitud_registro=longitud_registro, imagen_perfil=profile_image)
			update_last_connection(new_user_data)
			return UserSerializer(new_user_data).data

def usuario_getProfile(token,user_uid):

		if check_user_logged_in(token):
			try:
				fetch_user = Usuario.objects.get(uid=user_uid)
				return Response(UserProfileSerializer(fetch_user).data, status=status.HTTP_200_OK)
			except:
				return Response(status=status.HTTP_404_NOT_FOUND)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)

def GetOtherUserProfile(user_uid):
	try:
		return Usuario.objects.get(uid=user_uid)
	except:
		return None

def usuario_getvaloraciones(user_uid):
	try:
		if user_uid == 'nothing':
			return None
		else:
			user = Usuario.objects.get(uid=user_uid)
			ratings = ValidacionEstrella.objects.filter(usuario_valorado=user)
			return ValidacionEstrellaSerializer(ratings, many=True).data
	except:
		return None


def GetNotifications(token):
	try:
		user = get_user(token)
		if user != None:
			notifications = NotificacionesPendientes.objects.filter(usuario_pendiente__uid=user.uid)
			return NotificationSerializer(notifications, many=True).data
		else:
			return 'NOT FOUND'
	except:
		return 'NOT FOUND'

def GetBasicInfo(user_uid):
	if user_uid == 'nothing':
		return None
	else:
		try:
			return UserSerializer(Usuario.objects.get(uid=user_uid)).data
		except:
			return None