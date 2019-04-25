from bookalo.models import *
from django.contrib.auth.models import User
from django.db.models import Q
import json
import math


def get_usuario(user_uid):
    return User.objects.get(uid=user_uid)


def usuario_eliminar(user_uid):
    try:
        usuario = User.objects.get(uid=user_uid)
        usuario.delete()
        return True
    except Exception as e:
        print("No se ha podido eliminar el usuario")
        print (e.message)
        return False

def fetch_productos_usuario(usuario):
    lista_productos = Producto.objects.filter(vendido_por = usuario)
    return lista_productos


def fetch_productos_favoritos(usuario):
    lista_favoritos = Producto.objects.filter(le_gusta_a= usuario)
    return lista_favoritos

'''
    Pre: 	id_usuario corresponde al identificador de un usuario
            registrado en el sistema.
    Post: 	Devuelve una lista no ordenada las valoraciones estrella asociadas a un usuario con id ID_usuario
'''

def fetch_usuario_opiniones(usuario):
    return ValidacionEstrella.objects.filter(usuario_valorado = usuario) 
'''
    Pre: 	ID_usuario corresponde al identificador de un usuario
            registrado en el sistema.
    Post: 	Devuelve una lista no ordenada de datos de tipo Producto
            que tiene el usuario en en venta.
'''

def fetch_productos_usuario_venta(usuario):
    return Producto.objects.filter(Q(vendido_por = usuario) & Q(estado_producto = 'En venta')).distinct()


'''
    La clase filtro guarda los diferentes aspectos 
    asociados a la búsqueda de un producto en la 
    aplicacion
'''
'''
class filtro:
    String nombre_buscado
    float precio_minimo
    float precio_maximo
    float latitud_usuario
    float longitud_usuario
    int valoracion_minima
    int radio_busqueda
    String listaTags = []

    def __init__ (self,lectura):
        self.__dict__ = json.load(lectura)


'''
    Pre: x1,x2,x2,y2 corresponde a las 
'''
def calcular_distancia(x1,y1,x2,y2):
    return = math.sqrt( ((x1-x2)**2)+((y1-y2)**2) )

# -- Interaccion productos
'''
    Pre:	lectura contiene un cadena de texto tipo JSON (Objeto serializado) con los siguientes datos:
            '{	"nombre_buscado", "precio_minimo": "precio_maximo", "latitud_usuario", "longitud_usuario" ,"valoracion_minima",
            "radio_busqueda" , "tag_1","tag_2","tag_n" }'
    Post:	Devuelve un objeto parametros con los productos deserializados. La clase parametros únicamente contendrá los parametros
            extraídos del filtro.
            Ejemplo: https://stackoverflow.com/questions/15476983/deserialize-a-json-string-to-an-objects-in-python 
'''

def fetch_deserializar(lectura):
    return ( j = filtro(lectura) ) 

'''
    Pre:	Filtro contiene un cadena de texto tipo JSON (Objeto serializado) con los siguientes datos:
            '{	"nombre_buscado", "precio_minimo": "precio_maximo", "latitud_usuario", "longitud_usuario" , "radio_busqueda"
            "tag_1","tag_2","tag_n" }'
            Ejemplo de uso: https://www.analyticslane.com/2018/07/16/archivos-json-con-python/ 

    Post: 	Devuelve una lista de productos de acuerdo a los parámetros del filtro.
'''

def fetch_productos_filtro(filtro):
    return True

    
'''
    Pre:	True
    Post: 	Añade una lista de tags al producto, en caso de no existir el tag previamente lo añade en la base de datos
'''
def fetch_productos_anyadirtags(lista_tags,ID_producto):
    try:
        producto = Producto.objects.get(id = ID_producto)
        for tag in lista_tags:
            producto.tiene_tags.add(tag)
    except Exception as e:
        print("No se ha podido añadir la lista de tags")
        print(e.message)
        return False
    return True




'''
    Pre:	nombre_producto , ID_usuario son datos válidos de usuarios registrado y un producto asociado a él.
    Post:	Cambia el estado del producto nombre_producto a 'Reservado' y activa un timeout para posteriormetne 
            se haga un valoración del mismo
'''
def productos_reservar(nombre_producto,ID_usuario):
    try:
        producto = Producto.objects.get(id = ID_producto).update(estadoProducto = 'Reservado')
    except Exception as e:
        print ("No se ha podido modificar el estado del producto")
        print(e.message)
        return False
    return True


'''
    Pre:	ID_producto , ID_usuario son datos válidos de usuarios registrado y un producto asociado a él.
    Post:	Cambia el estado del producto nombre_producto a 'en venta' y activa un timeout para posteriormente 
            se haga un valoración del mismo ( Observar framework detalle chat).
'''
def productos_quitarReserva(ID_producto,ID_usuario):
    try:
        producto = Producto.objects.get(id = ID_producto).update(estadoProducto = 'En Venta')
    except Exception as e:
        print ("No se ha podido modificar el estado del producto")
        print(e.message)
        return False
    return True



'''
    Pre:	nuevoProducto es un Producto creado previamente
    Post:	Asocia los campos de nuevoProducto al Producto nombre_producto del usuario con nombre usuario.
'''
def productos_modificarProducto( ID_producto, nuevoProducto):
    try:
        producto = Producto.objects.get(id = ID_producto)
        producto.delete()
        nuevoProducto.update(id = ID_producto)
        nuevoProducto.save()
    except Exception as e:
        print ("No se ha podido modificar el estado del producto")
        print(e.message)
        return False
    return True


# -- 	Interaccion  tags ------------------------------------------


'''
    Pre: 	True
    Post: 	Devuelve una list<tags> que contiene una serie tags predeterminados del sitema ()
'''
def tags_predeterminados():
    return Tag.filter.objects(es_predeterminado = 'T')

'''
    Pre: 	nombre_tag es un String no vacio
    Post: 	Anade un tag a la base de datos con nombre nombre_tag
'''
def tags_anyadir(nombre_tag):
    Tag = Tag(nombre = nombre_tag)
    Tag.save()
    return True
'''
    Pre: 	True
    Post: 	Devuelve una lista de los 10 tags más usuados, en caso de no existir 10 tags devoverá 
            el número que se encuentre en la base de datos.
'''
def tags_topTags():
    lista=Tag.objects.annotate(tag_count=Count('nombre')).order_by('-tag_count')[:10]
    return lista


# -- 	Interaccion  Chat ------------------------------------------

'''
    Pre: 	ID_comprador e ID_vendedor contiene dos identificadores válidos de usuarios registrados diferentes.
    Post: 	Crea  un chat vacio entre dos usuarios 
'''
def chat_crear(ID_comprador, ID_vendedor, ID_producto):
    try:
        chat=Chat(vendedor=ID_vendedor, comprador=ID_comprador, producto=ID_producto)
        chat.save()
    except Exception as e:
        print ("No se ha podido crear el chat")
        print(e.message)
        return False
    return True


'''
    Pre: 	ID es un identificador de un chat guardado en la base de datos.
    Post: 	Añade el mensaje al chat con identificador ID con la hora especificada.
'''
def chat_anyadirMensaje( ID, mensaje, hora):
    try:
        men=Mensaje(texto=mensaje, hora=hora, chat_asociado=ID)
        men.save()
    except Exception as e:
        print ("No se ha podido crear el chat")
        print(e.message)
        return False
    return True

'''
    Pre: 	ID es un identificador de un chat guardado en la base de datos.
    Post: 	Devuelve una lista de mensajes del chat identificado con ID, ordenados por hora
'''
def chat_devolverChat(ID):
    mensajes=Mensaje.objects.filter(chat_asociado=ID).order_by('-hora')
    return mensajes


# -- 	Interaccion  Elemento Multimedia ------------------------------------------

'''
    Pre: 	path contiene la ruta relativa o absoluta a un archivo multimedia,  nombre_producto
            corresponden a campos para la identificación de un producto registrado en el sistema.
    Post: 	Crear una instancia en la base de datos para ese producto y le asocia un identificador y el producto
            al cual esta asociado.
'''

def ContenidoMultimedia_crear(multimedia,ID_producto):
    try:
        multi=ContenidoMultimedia(contenido=multimedia, producto=ID_producto)
        multi.save()
    except Exception as e:
        print ("No se ha podido subir el archivo")
        print(e.message)
        return False
    return True


'''
    Pre: 	ID_multimedia contiene el identificador de un elemento de contenido multimedia creado previamente y path
            contiene la ruta hacia el contenido multimedia.
    Post: 	Modifica la ruta del ContenidoMultimedia con identificador ID_multimedia.
'''
def ContenidoMultimedia_modificar(ID_multimedia, pathProducto):
    try:
        ContenidoMultimedia.objects.filter(id=ID_multimedia).update(contenido_url=pathProducto)
    except Exception as e:
        print ("No se ha podido actualizar el archivo")
        print(e.message)
        return False
    return True

'''
    Pre: 	ID_multimedia contiene el identificador de un elemento de contenido multimedia creado previamente.
    Post: 	Elimina el ContenidoMultimedia identificado con ID_multimedia.
'''
def ContenidoMultimedia_eliminar(ID_multimedia):
    try:
        ContenidoMultimedia.objects.filter(id=ID_multimedia).delete()
    except Exception as e:
        print ("No se ha podido borrar el archivo")
        print(e.message)
        return False
    return True

# 	------------------------------------ IDS corregidos -----------------------------

# -- 	Interaccion  Valoracion Estrella ------------------------------------------

'''
    Pre: 	ID_usuario contiene el identificador de un usuario registrado, ya sea que valora o es valorado
            y calificacion contiene un valor decimal [0,5]

    Post: 	Crear una instancia en la base de datos ue asocia una valoración a un usuario
'''

def valoracionEstrella_anyadir(ID_usuario_valorado, ID_usuario_quevalora, calificacion):
    try:
        estrella = ValidacionEstrella(usuario_valorado=ID_usuario_valorado, usuario_que_valora=ID_usuario_quevalora, estrellas=calificacion)
        estrella.save()
    except Exception as e:
        print ("No se ha podido crear la valoracion estrella")
        print(e.message)
        return False
    return True

'''
    Pre: 	ID_usuario contiene el identificador de un usuario registrado .

    Post: 	Devuelve una lista que contiene las valoraciones asociadas a un usuaro
'''
def valoracionEstrella_lista_usuario(ID_usuario):
    lista = ValidacionEstrella.objects.filter(usuario_valorado=ID_usuario).distinct()
    return lista

'''
    Pre: 	ID_usuario contiene el identificador de un usuario registrado .

    Post: 	Devuelve un valor decimal [0-5] que contiene la valoración media de un usuario
'''
def valoracionEstrella_usuario(ID_usuario):
    lista = valoracionEstrella_lista_usuario(ID_usuario)
    media=0
    counter=0
    for val in lista:
        media += val.estrellas
        counter+=1
    return media/counter

'''
    Pre: 	ID_usuario contiene el identificador de un usuario registrado, ya sea que valora o es valorado
            y un string que es un comentario a asociar

    Post: 	Crear una instancia en la base de datos que asocia un comentario a un usuario en concreto
'''

def valoracionProducto_anyadir(ID_usuario_valorado, ID_usuario_quevalora, comentario):
    try:
        estrella = ValidacionProducto(usuario_valorado=ID_usuario_valorado, usuario_que_valora=ID_usuario_quevalora, comentario=comentario)
        estrella.save()
    except Exception as e:
        print ("No se ha podido crear la valoracion de producto")
        print(e.message)
        return False
    return True

# TODO: Revision de reportes?

'''
    Pre: 	causa contiene un String no vacio e ID_usuario el identificador de un usuario registrado en el sistema.

    Post: 	Crear una instancia en la base de datos que asocia un nuevo reporte con una Causa causa
            y un identificador.
'''

def Report_anyadir(ID_usuario, causa):
    try:
        repo = Report(usuario_reportado=ID_usuario, causa=causa)
        repo.save()
    except Exception as e:
        print ("No se ha podido crear la el report")
        print(e.message)
        return False
    return True



# -- 	Interaccion  Firebase  ------------------------------------------
'''
