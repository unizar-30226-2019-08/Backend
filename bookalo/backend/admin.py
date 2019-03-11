from django.contrib import admin
from backend.models import *
from django.forms.models import BaseInlineFormSet

#Modelos que apareceran en el portal de administracion
admin.site.register(Tag)
admin.site.register(Producto)
admin.site.register(ContenidoMultimedia)
admin.site.register(Chat)
admin.site.register(Mensaje)
admin.site.register(Report)
admin.site.register(ValidacionProducto)
admin.site.register(ValidacionEstrella)