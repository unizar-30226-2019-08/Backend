from bookalo.models import *
from bookalo.serializers import *
from .views import *


def CrearChat(token,otroUserUid,productId):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	otroUser = Usuario.objects.get(uid=otroUserUid)
	product = Producto.objects.get(id=productId)
	chat = Chat.objects.create(vendedor=otroUser, comprador=user, producto=product)