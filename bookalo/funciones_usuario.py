from bookalo.models import *
from bookalo.serializers import *
from .views import *
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal

#Comprueba que el usuario este logeado en el sistema
def check_user_logged_in(token):
	try:
		user_info = auth.get_account_info(token)
		user_uid = user_info['users'][0]['localId']
		user = Usuario.objects.get(uid=user_uid).update(ultima_conexion=datetime.now)
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
			name = user_info['users'][0]['email'].split("@")[0]
		except:	
			return 'Error'
		
		try:
			user = Usuario.objects.get(uid=user_uid)
			user.ultima_conexion = datetime.now()
			user.save(update_fields=['ultima_conexion'])

			if user.esta_baneado:
				return Response(UserSerializer(user).data, status=status.HTTP_401_UNAUTHORIZED)
			else:
				update_last_connection(user)
				return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

		except Usuario.DoesNotExist:

			new_user_data = Usuario.objects.create(uid=user_uid, nombre=name, latitud_registro=latitud_registro, longitud_registro=longitud_registro)
			return Response(UserSerializer(new_user_data).data, status=status.HTTP_201_CREATED)

def usuario_getProfile(token):
	if request.method != 'POST':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	if token == 'nothing' or user_uid == 'nothing':
		return Response(status=status.HTTP_400_BAD_REQUEST)
	else:
		#if check_user_logged_in(token):
			#try:
				fetch_user = Usuario.objects.get(uid=user_uid)
				return Response(UserProfileSerializer(fetch_user).data, status=status.HTTP_200_OK)
			#except:
			#	return Response(status=status.HTTP_404_NOT_FOUND)
		#else:
		#	return Response(status=status.HTTP_401_UNAUTHORIZED)


