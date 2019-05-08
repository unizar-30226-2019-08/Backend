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
		Mensaje.objects.create(texto=message, chat_asociado=chat, emisor=user)
		return True
	except:
		return False	

def GetUserMessages(chat_pk, user):
	try:
		messages = Mensaje.objects.filter(chat_asociado__pk=chat_pk)
		return MensajeSerializer(messages, many=True, read_only=True, context = {"user": user})
	except:
		return None