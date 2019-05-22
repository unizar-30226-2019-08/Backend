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
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.timezone import now as timezone_now
from geopy import Nominatim
from fcm_django.models import FCMDevice
import itertools

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

def session_needs_deleting(session):
	try:
		ahora = timezone_now()
		ahora = ahora.replace(tzinfo=None)
		fecha_creacion = session.timestamp
		result = relativedelta(ahora, fecha_creacion)
		if result.days >= 1:
			return True
		else:
			return not check_user_logged_in(session.token)
	except:
		return False

def usuario_login(token, token_fcm, latitude, longitude, fcm_type, movil):
	if latitude == '-1':
		latitud_registro = 41.683490
	else:
		latitud_registro = Decimal(latitude)

	if longitude == '-1':
		longitud_registro = -0.888479
	else:
		longitud_registro = Decimal(longitude)
	
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
			geolocator = Nominatim(user_agent="bookalo")
			location = geolocator.reverse(str(latitud_registro) + ',' + str(longitud_registro))
			try:
				ciudad = location.raw['address']['city']
			except:
				ciudad = location.raw['address']['county']
		except:
			ciudad = 'Zaragoza'
		try:
			user = Usuario.objects.get(uid=user_uid)
			
			if user.esta_baneado:
				return status.HTTP_401_UNAUTHORIZED
			else:
				user.latitud_registro = latitud_registro
				user.longitud_registro = longitud_registro
				user.ciudad = ciudad
				user.save()
				update_last_connection(user)
				try:
					if movil == 'true':
						es_movil = True
					else:
						es_movil = False
					sessions = Sesion.objects.filter(usuario=user)
					if sessions:
						for session in sessions:
							if session_needs_deleting(session):
								session.delete()
						user = Usuario.objects.get(uid=user_uid)
						try:
							sesion = Sesion.objects.get(token_fcm=token_fcm, usuario=user)
							sesion.token = token
							sesion.save()
						except Exception as ex:
							Sesion.objects.create(token=token, token_fcm=token_fcm, usuario=user, es_movil=es_movil)
					else:
						try:
							user = Usuario.objects.get(uid=user_uid)
							Sesion.objects.create(token=token, token_fcm=token_fcm, usuario=user, es_movil=es_movil)
						except Exception as ex:
							user = Usuario.objects.get(uid=user_uid)
							Sesion.objects.create(token=token, token_fcm=str(ex), usuario=user, es_movil=es_movil)
				except Exception as ex:
					print("Error while looking for active sessions")
				return UserSerializer(user).data

		except Usuario.DoesNotExist:

			new_user_data = Usuario.objects.create(username=user_uid, uid=user_uid, token_fcm=token_fcm, nombre=name, latitud_registro=latitud_registro, longitud_registro=longitud_registro, imagen_perfil=profile_image, ciudad=ciudad)
			Sesion.objects.create(token=token, token_fcm=token_fcm, usuario=new_user_data)
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

def usuario_getvaloraciones(user_uid,ultimo_indice,elementos_pagina):
	try:
		if user_uid == 'nothing':
			return None
		else:
			user = Usuario.objects.get(uid=user_uid)
			ratings = ValidacionEstrella.objects.filter(usuario_valorado=user)
			ultimo_indice = int(ultimo_indice)
			elementos_pagina = int(elementos_pagina)
			if(elementos_pagina != -1):
				ratings = itertools.islice(ratings, ultimo_indice, ultimo_indice + elementos_pagina)
			serializador = ValidacionEstrellaSerializer(ratings, many=True, context = {"user": user})
			return serializador.data
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