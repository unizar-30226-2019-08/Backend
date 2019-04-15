from bookalo.models import *
from bookalo.serializers import *
from .views import *
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal

def calculate_distance(lat1, lon1, lat2, lon2):
	R = 6373.0
	lat1_rad = radians(lat1)
	lon1_rad = radians(lon1)
	lat2_rad = radians(lat2)
	lon2_rad = radians(lon2)

	dlon = lon2_rad - lon1_rad
	dlat = lat2_rad - lat1_rad
	a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	return R * c


def GenericProducts():
	products = Producto.objects.order_by('-num_likes')
	serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def BusquedaProducto(search):
	preposiciones = ['a','ante','bajo','cabe','con','contra','de','desde','en','entre',
	'hacia','hasta','para','por','segun','sin','so','sobre','tras']
	products = Producto.objects.none()
	for word in search.split():
		if word not in preposiciones:
			productos_palabra = Producto.objects.filter(nombre__contains=word)
			products = products | productos_palabra
	products.distinct()
	serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def ProductosUsuario(token):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	products = Producto.objects.filter(vendido_por=user)
	serializer = ProductoSerializerList(products, many=True, read_only=True)
	return serializer

def FiltradoProducto(request):
	tags = request.POST.get('tags', '')

	user_latitude = request.POST.get('latitud', '')
	user_longitude = request.POST.get('longitud', '')
	max_distance = request.POST.get('distancia_maxima', '')
	min_price = request.POST.get('precio_minimo', '')
	max_price = request.POST.get('precio_maximo', '')
	min_score = request.POST.get('calificacion_minima', '')
	if tags == '' or user_latitude == '' or user_longitude == '' or max_distance == '' or min_price == '' or max_price == '' or min_score == '':
		return 'Bad request'

	lista_tags = [x.strip() for x in tags.split(',')]
	tag_queryset = Tag.objects.filter(nombre__in=lista_tags)
	products = Producto.objects.filter(precio__lte=Decimal(max_price), precio__gte=Decimal(min_price), vendido_por__media_valoraciones__gte=min_score, tiene_tags__in=tag_queryset)

	filtered_products = []
	for product in products:
		print(product.nombre)
		if Decimal(max_distance) >= calculate_distance(Decimal(product.latitud), Decimal(product.longitud), Decimal(user_latitude), Decimal(user_longitude)):
			filtered_products.append(product)
	serializer = ProductoSerializerList(filtered_products, many=True, read_only=True)
	return serializer


def CreacionProducto(request,token):
	#Cambiar esto
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']	
	user = Usuario.objects.get(uid=user_uid)
	if user == None:
		return 'Not found'
	#Get all the required parameters for the product
	files = request.FILES.items()
	latitud = request.POST.get('latitud', '')
	longitud = request.POST.get('longitud', '')
	nombre = request.POST.get('nombre', '')
	precio = request.POST.get('precio', '')
	estado_producto = request.POST.get('estado_producto', '')
	tipo_envio = request.POST.get('tipo_envio', '')
	descripcion = request.POST.get('descripcion', '')
	tags = request.POST.get('tags', '')
	#Check that the request is correct
	if latitud == '' or longitud == '' or nombre == '' or precio == '' or estado_producto == '' or tipo_envio == '' or descripcion == '' or tags == '':
		return 'Bad request'
	tag_pk = []
	estado_producto = EleccionEstadoProducto(estado_producto)
	lista_tags = [x.strip() for x in tags.split(',')]
	for tag in lista_tags:
		tag_obj,created = Tag.objects.get_or_create(nombre=tag)
		tag_pk.append(tag_obj.pk)
	producto = Producto(vendido_por=user, 
						latitud=Decimal(latitud), 
						longitud=Decimal(longitud), 
						nombre=nombre, 
						precio=Decimal(precio), 
						estado_producto=estado_producto, 
						estado_venta=EleccionEstadoVenta.en_venta,
						tipo_envio=tipo_envio,
						descripcion=descripcion)
	producto.save()
	producto.tiene_tags.set(tag_pk)
	i = 0
	for file,created in files:
		multi = ContenidoMultimedia(contenido=file, producto=producto, orden_en_producto=i)
		multi.save()
		i = i + 1
	return 'Created'


def BorradoProducto(token,productId):
	user_info = auth.get_account_info(token)
	user_uid = user_info['users'][0]['localId']
	user = Usuario.objects.get(uid=user_uid)
	product = Producto.objects.get(id=productId)
	if product.vendido_por == user:
		product.delete()
		return 'Ok'
		return Response(status=status.HTTP_200_OK)
	else:
		return 'Unauthorized'
		return Response(status=status.HTTP_401_UNAUTHORIZED)

