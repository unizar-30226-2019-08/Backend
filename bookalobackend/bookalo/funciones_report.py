from bookalo.models import *
from bookalo.serializers import *
from .views import *

def CrearReport(reporteduserUid,comment):
	reporteduser = Usuario.objects.get(uid=reporteduserUid)
	reporte = Report.objects.create(usuario_reportado=reporteduser, causa=comment)
