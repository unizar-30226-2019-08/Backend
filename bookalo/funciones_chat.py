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
from .funciones_usuario import *
import itertools
from fcm_django.models import FCMDevice
import requests
import json

def CrearChat(token,otroUserUid,productId):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	otroUser = Usuario.objects.get(uid=otroUserUid)
	product = Producto.objects.get(pk=int(productId))
	#Comprobamos que no exista el chat previamente
	try:
		chat = Chat.objects.get(vendedor=otroUser, comprador=user, producto=product)
	except:
		chat = Chat.objects.create(vendedor=otroUser, comprador=user, producto=product)
	return chat

def GetChatVendedor(user,ultimo_indice,elementos_pagina):
	chats = Chat.objects.filter(vendedor=user)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		chats = itertools.islice(chats, ultimo_indice, ultimo_indice + elementos_pagina)
	return ChatSerializer(chats, many=True, read_only=True)

def GetChatComprador(user,ultimo_indice,elementos_pagina):
	chats = Chat.objects.filter(comprador=user)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		chats = itertools.islice(chats, ultimo_indice, ultimo_indice + elementos_pagina)
	return ChatSerializer(chats, many=True, read_only=True)



def CrearMensaje(token, chat_id, message):
	try:
		user = get_user(token)
		chat = Chat.objects.get(pk=int(chat_id))
		mensaje = Mensaje(texto=message, chat_asociado=chat, emisor=user)
		mensaje.save()
		return mensaje
	except:
		return None	

def CrearNotificiacion(usuario, message):
	try:
		NotificacionesPendientes.objects.create(usuario_pendiente=usuario, descripcion_notificacion=message)
		return True
	except:
		return False

def GetUserMessages(chat_pk, user):
	try:
		messages = Mensaje.objects.filter(chat_asociado__pk=chat_pk).order_by('hora')
		return MensajeSerializer(messages, many=True, read_only=True, context = {"user": user})
	except:
		return None

def GetChatInfoWeb(chat_id):
	try:
		chat = Chat.objects.get(pk=int(chat_id))
		product = chat.producto
		seller = chat.vendedor
		buyer = chat.comprador
		return {'comprador':UserSerializer(buyer).data, 'vendedor':UserSerializer(seller).data, 'producto': ProductoSerializer(product).data}
	except:
		return {'comprador': '', 'vendedor':'', 'producto': ''}

def SendFCMMessage(chat_id, message, token, emisor, soy_vendedor):
	try:
		chat_obj = Chat.objects.get(pk=int(chat_id))
		chat = ChatSerializer(chat_obj).data
		mensaje = {
			"texto":message.texto,
			"timestamp":message.hora
		}
		URL = 'https://fcm.googleapis.com/fcm/send'
		data = {
			"registration_ids":[token],
			"notification":{
				"title":emisor.nombre + ' - ' + chat_obj.producto.nombre,
				"body":message.texto
			},
			"data":{
				"chat":chat,
				"soy_vendedor":soy_vendedor,
				"mensaje":mensaje
			}
		}
		data = json.dumps(data)
		headers = {"Authorization":"key=AAAARwXiWF8:APA91bEvM5nPUaBpR217T3ZjRqCGvYadxmHQXQSIgGMkWn_BeAOnnLZNv2DtVmCwF-D_sJEsh4CrDg6S0S4jl9tsImUnqzEGAssiizIF4U1h0AVsgyzzU8to0q0QlLx2cFu2673OvKuH","Content-Type":"application/json"}
		r = requests.post(url=URL, data=data, headers=headers)
		data = {
			"registration_ids":[token],
			"notification":{
				"title":"Soy el mensaje de correccion",
				"body":r.text
			}
		}
		r = requests.post(url=URL, data=data, headers=headers)
		return True
	except:
		return False
