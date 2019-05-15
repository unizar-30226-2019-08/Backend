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
		try:
			chat = Chat.objects.get(pk=int(chat_pk))
			if chat.vendedor == user:
				chat.num_pendientes_vendedor = 0
				chat.save()
			elif chat.comprador == user:
				chat.num_pendientes_comprador = 0
				chat.save()
			else:
				chat.save()
			messages = Mensaje.objects.filter(chat_asociado__pk=chat_pk).order_by('hora')
			return MensajeSerializer(messages, many=True, read_only=True, context = {"user": user})
		except:
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
		headers = {"Authorization":"key=AAAARwXiWF8:APA91bEvM5nPUaBpR217T3ZjRqCGvYadxmHQXQSIgGMkWn_BeAOnnLZNv2DtVmCwF-D_sJEsh4CrDg6S0S4jl9tsImUnqzEGAssiizIF4U1h0AVsgyzzU8to0q0QlLx2cFu2673OvKuH","Content-Type":"application/json"}
		URL = 'https://fcm.googleapis.com/fcm/send'
		chat_obj = Chat.objects.get(pk=int(chat_id))
		if chat_obj.vendedor == emisor:
			chat_obj.num_pendientes_vendedor = chat_obj.num_pendientes_vendedor + 1
			chat_obj.save()
		else:
			chat_obj.num_pendientes_comprador = chat_obj.num_pendientes_comprador + 1
			chat_obj.save()
		chat = ChatSerializer(chat_obj).data
		mensaje = {
			"texto":message.texto,
			"timestamp":str(message.hora)
		}
		data = {
			"registration_ids":[token],
			"notification":{
				"title":emisor.nombre + ' - ' + chat_obj.producto.nombre,
				"body":message.texto
			},
			"data":{
				"chat":chat,
				"soy_vendedor":soy_vendedor,
				"mensaje":mensaje,
				"es_mio":False
			}
		}
		data = json.dumps(data)
		r = requests.post(url=URL, data=data, headers=headers)
		data = {
			"registration_ids":[token],
			"notification":{
				"title":"Mensaje de DEBUG",
				"body":"Output de FCM: " + r.text
			}
		}
		data = json.dumps(data)
		r = requests.post(url=URL, data=data, headers=headers)
		return True
	except Exception as ex:
		data = {
			"registration_ids":[token],
			"notification":{
				"title":"Bookalo: Fallo en recepción",
				"body":"Un error ocurrió mientras recibías el mensaje: " + str(ex)
			}
		}
		data = json.dumps(data)
		r = requests.post(url=URL, data=data, headers=headers)
		return False
