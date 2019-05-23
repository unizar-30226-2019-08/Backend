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
from django.core.mail import EmailMessage
from .funciones_chat import *

def CrearReport(reporteduserUid, cause, comment):
	reporteduser = Usuario.objects.get(uid=reporteduserUid)
	reporte = Report.objects.create(usuario_reportado=reporteduser, causa=cause, comentario=comment)
	return reporte

def MandarCorreo(user,reporteduserUid, cause, comment, id_chat):
	try:
		correo = 'robertabookalo@gmail.com'
		reporteduser = Usuario.objects.get(uid=reporteduserUid)
		mensaje = 'El usuario ' + reporteduser.nombre + ' con uid ' + reporteduser.uid + ' y una media de valoraciones de ' + str(reporteduser.media_valoraciones) + ', ha sido reportado por el usuario ' + user.nombre + ' con uid ' + user.uid + '\nCausa: ' + cause + '\nComentario del usuario: ' + comment + '.'
		if id_chat != 'nothing':
			chat = Chat.objects.get(id=int(id_chat))
			mensaje = mensaje + '\n\nMensajes del chat:'
			mensajes_chat = Mensaje.objects.filter(chat_asociado=chat).order_by('-hora')
			for m in mensajes_chat:
				hora_mensaje = str(m.hora.year)+ '-' + str(m.hora.month) + '-' + str(m.hora.day) + '  ' + str(m.hora.hour) +':'+ str(m.hora.minute) +':'+ str(m.hora.second)
				mensaje = mensaje +'\n' + m.emisor.nombre +',' + hora_mensaje + ': ' + m.texto
		email = EmailMessage('Reporte de usuario ' + reporteduser.nombre, mensaje, 
				to=[correo])
		email.send()
		return True
	except:
		return False