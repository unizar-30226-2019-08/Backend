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

def get_list_tokens(user, token_to_omit):
	sessions = Sesion.objects.filter(usuario=user, es_movil=True)
	tokens_movil = []
	for session in sessions:
		if session.token != token_to_omit:
			tokens_movil = tokens_movil + [session.token_fcm]

	sessions = Sesion.objects.filter(usuario=user, es_movil=False)
	tokens_web = []
	for session in sessions:
		if session.token != token_to_omit:
			tokens_web = tokens_web + [session.token_fcm]
	return {'movil':tokens_movil, 'web':tokens_web}

def get_list_tokens_without_sender(user, token_to_omit):
	sessions = Sesion.objects.filter(usuario=user, es_movil=True)
	tokens_movil = []
	for session in sessions:
		if session.token_fcm != token_to_omit:
			tokens_movil = tokens_movil + [session.token_fcm]

	sessions = Sesion.objects.filter(usuario=user, es_movil=False)
	tokens_web = []
	for session in sessions:
		if session.token_fcm != token_to_omit:
			tokens_web = tokens_web + [session.token_fcm]
	return {'movil':tokens_movil, 'web':tokens_web}


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
	chats = Chat.objects.filter(vendedor=user, borrado_vendedor=False, producto__estado_venta=True)
	chats_terminados = Chat.objects.filter(vendedor=user, borrado_vendedor=False, producto__estado_venta=False)
	chats = list(chats) + list(chats_terminados)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		chats = itertools.islice(chats, ultimo_indice, ultimo_indice + elementos_pagina)
	return ChatSerializer(chats, many=True, read_only=True, context = {"user": user})

def GetChatComprador(user,ultimo_indice,elementos_pagina):
	chats = Chat.objects.filter(comprador=user,borrado_comprador=False, producto__estado_venta=True)
	chats_terminados = Chat.objects.filter(comprador=user,borrado_comprador=False, producto__estado_venta=False)
	chats = list(chats) + list(chats_terminados)
	ultimo_indice = int(ultimo_indice)
	elementos_pagina = int(elementos_pagina)
	if(elementos_pagina != -1):
		chats = itertools.islice(chats, ultimo_indice, ultimo_indice + elementos_pagina)
	return ChatSerializer(chats, many=True, read_only=True, context = {"user": user})



def CrearMensaje(token, chat_id, message):
	try:
		user = get_user(token)
		chat = Chat.objects.get(pk=int(chat_id))
		mensaje = Mensaje(texto=message, chat_asociado=chat, emisor=user)
		mensaje.save()
		chat.borrado_vendedor = False
		chat.borrado_comprador = False
		chat.save()
		return mensaje
	except:
		return None	

def CrearNotificiacion(usuario, message):
	try:
		NotificacionesPendientes.objects.create(usuario_pendiente=usuario, descripcion_notificacion=message)
		return True
	except:
		return False

def GetUserMessages(chat_pk, user,ultimo_indice,elementos_pagina):
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
			ultimo_indice = int(ultimo_indice)
			elementos_pagina = int(elementos_pagina)
			if(elementos_pagina != -1):
				messages = Mensaje.objects.filter(chat_asociado__pk=chat_pk).order_by('-hora')
				messages = itertools.islice(messages, ultimo_indice, ultimo_indice + elementos_pagina)
			else:
				messages = Mensaje.objects.filter(chat_asociado__pk=chat_pk).order_by('hora')
			return MensajeSerializer(messages, many=True, read_only=True, context = {"user": user})
		except:
			messages = Mensaje.objects.filter(chat_asociado__pk=chat_pk).order_by('hora')
			if(elementos_pagina != -1):
				messages = itertools.islice(messages, ultimo_indice, ultimo_indice + elementos_pagina)
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

def BorradoChat(token,chatId):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	chat = Chat.objects.get(id=chatId)
	if chat.vendedor == user:
		chat.borrado_vendedor = True
		chat.save()
		if chat.borrado_comprador == True:
			chat.delete()
		return 'Ok'
	elif chat.comprador == user:
		chat.borrado_comprador = True
		chat.save()
		if chat.borrado_vendedor == True:
			chat.delete()
		return 'Ok'
	else:
		return 'Unauthorized'

def SendFCMMessage(chat_id, message, token_emisor, emisor, soy_vendedor, receptor):
	try:
		headers = {"Authorization":"key=AAAARwXiWF8:APA91bEvM5nPUaBpR217T3ZjRqCGvYadxmHQXQSIgGMkWn_BeAOnnLZNv2DtVmCwF-D_sJEsh4CrDg6S0S4jl9tsImUnqzEGAssiizIF4U1h0AVsgyzzU8to0q0QlLx2cFu2673OvKuH","Content-Type":"application/json"}
		URL = 'https://fcm.googleapis.com/fcm/send'
		chat_obj = Chat.objects.get(pk=int(chat_id))
		if chat_obj.vendedor == emisor:
			chat_obj.num_pendientes_comprador = chat_obj.num_pendientes_comprador + 1
			chat_obj.save()
		else:
			chat_obj.num_pendientes_vendedor = chat_obj.num_pendientes_vendedor + 1
			chat_obj.save()

		#Codigo para el receptor del mensaje
		chat = ChatSerializer(chat_obj, context = {"user": receptor}).data
		mensaje = MensajeSerializer(message, context = {"user": receptor}).data
		tokens_receptor = get_list_tokens(receptor, "NONE")
		if tokens_receptor['movil']:
			data = {
				"notification":{
					"title":"Bookalo",
					"body":"¡Hola " + receptor.nombre + "! La venta se ha cerrado para el producto " + chat_obj.producto.nombre + ". ¡Valora a " + emisor.nombre + "!",
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_receptor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
			data = {
				"registration_ids":tokens_receptor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
		if tokens_receptor['web']:
			data = {
				"notification":{
					"title":"Bookalo",
					"body":"¡Hola " + receptor.nombre + "! La venta se ha cerrado para el producto " + chat_obj.producto.nombre + ". ¡Valora a " + emisor.nombre + "!",
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_receptor['web'],
				"data":{
					"chat":chat,
					"soy_vendedor":soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)

		#Codigo para el emisor del mensaje
		chat = ChatSerializer(chat_obj, context = {"user": emisor}).data
		mensaje = MensajeSerializer(message, context = {"user": emisor}).data
		tokens_emisor = get_list_tokens(emisor, token_emisor)
		if tokens_emisor['movil']:
			data = {
				"registration_ids":tokens_emisor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":not soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
		if tokens_emisor['web']:
			data = {
				"notification":{
					"title":"Bookalo",
					"body":"¡Hola " + emisor.nombre + "! La venta se ha cerrado para el producto " + chat_obj.producto.nombre + ". ¡Valora a " + receptor.nombre + "!",
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_emisor['web'],
				"data":{
					"chat":chat,
					"soy_vendedor":not soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
		return True
	except Exception as ex:
		tokens_emisor = get_list_tokens(emisor, token_emisor)
		data = {
			"registration_ids":[tokens_emisor],
			"notification":{
				"title":"Bookalo: Fallo en envio de mensaje",
				"body":"Un error ocurrió mientras enviabas el mensaje - " + message.texto + " -: " + str(ex)
			}
		}
		data = json.dumps(data)
		requests.post(url=URL, data=data, headers=headers)
		return False

def SendFCMChatMessage(chat_id, message, token_emisor, emisor, soy_vendedor, receptor):
	try:
		headers = {"Authorization":"key=AAAARwXiWF8:APA91bEvM5nPUaBpR217T3ZjRqCGvYadxmHQXQSIgGMkWn_BeAOnnLZNv2DtVmCwF-D_sJEsh4CrDg6S0S4jl9tsImUnqzEGAssiizIF4U1h0AVsgyzzU8to0q0QlLx2cFu2673OvKuH","Content-Type":"application/json"}
		URL = 'https://fcm.googleapis.com/fcm/send'
		chat_obj = Chat.objects.get(pk=int(chat_id))
		if chat_obj.vendedor == emisor:
			chat_obj.num_pendientes_comprador = chat_obj.num_pendientes_comprador + 1
			chat_obj.save()
		else:
			chat_obj.num_pendientes_vendedor = chat_obj.num_pendientes_vendedor + 1
			chat_obj.save()

		#Codigo para el receptor del mensaje
		chat = ChatSerializer(chat_obj, context = {"user": receptor}).data
		mensaje = MensajeSerializer(message, context = {"user": receptor}).data
		tokens_receptor = get_list_tokens_without_sender(receptor, "NONE")
		if tokens_receptor['movil']:
			data = {
				"notification":{
					"title":emisor.nombre + ' - ' + chat_obj.producto.nombre,
					"body":message.texto,
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_receptor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":not soy_vendedor,
					"mensaje":mensaje,
					"click_action":"FLUTTER_NOTIFICATION_CLICK",
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
			data = {
				"registration_ids":tokens_receptor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":not soy_vendedor,
					"mensaje":mensaje,
					"click_action":"FLUTTER_NOTIFICATION_CLICK",
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
		if tokens_receptor['web']:
			data = {
				"notification":{
					"title":emisor.nombre + ' - ' + chat_obj.producto.nombre,
					"body":message.texto,
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_receptor['web'],
				"data":{
					"chat":chat,
					"soy_vendedor":not soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)

		#Codigo para el emisor del mensaje
		chat = ChatSerializer(chat_obj, context = {"user": emisor}).data
		mensaje = MensajeSerializer(message, context = {"user": emisor}).data
		tokens_emisor = get_list_tokens_without_sender(emisor, token_emisor)
		if tokens_emisor['movil']:
			data = {
				"notification":{
					"title":receptor.nombre + ' - ' + chat_obj.producto.nombre,
					"body":message.texto,
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_emisor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
			data = {
				"registration_ids":tokens_emisor['movil'],
				"data":{
					"chat":chat,
					"soy_vendedor":soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
		if tokens_emisor['web']:
			data = {
				"notification":{
					"title":emisor.nombre + ' - ' + chat_obj.producto.nombre,
					"body":message.texto,
					"icon":"https://bookalo.es/media/bookalo_logo.png"
				},
				"registration_ids":tokens_emisor['web'],
				"data":{
					"chat":chat,
					"soy_vendedor":soy_vendedor,
					"mensaje":mensaje,
				}
			}
			data = json.dumps(data)
			requests.post(url=URL, data=data, headers=headers)
		return True
	except Exception as ex:
		data = {
			"registration_ids":[token_emisor],
			"notification":{
				"title":"Bookalo: Fallo en envio de mensaje",
				"body":"Un error ocurrió mientras enviabas el mensaje - " + message.texto + " -: " + str(ex)
			}
		}
		data = json.dumps(data)
		requests.post(url=URL, data=data, headers=headers)
		return False
