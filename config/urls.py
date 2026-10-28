import json

from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path, include
from django.views.decorators.csrf import ensure_csrf_cookie

from config import settings


@ensure_csrf_cookie
def peticion_php(request):
    if request.method == "GET":
        print(get_token(request))
        return JsonResponse({
            "mensaje": "Estimado Robert usted está accediendo a mi servidor",
            "csrf_token": get_token(request),
        })

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {"error": "El cuerpo debe contener un JSON válido"},
                status=400,
            )

        print("Datos recibidos:", data, flush=True)

        return JsonResponse({
            "mensaje": "Datos recibidos correctamente"
        })

    return JsonResponse(
        {"error": "Método no permitido"},
        status=405,
        headers={"Allow": "GET, POST"},
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path("select2/", include("django_select2.urls")),
    path('', include('core.urls')),
    path('agenda/', include('agenda_telefonica.urls')),
    path('soporte/', include('soporte.urls')),
    path('horos/', include('horos.urls')),
    path('gestion/', include('gestion_tic.urls')),
    path('bodega/', include('bodega.urls')),
    path('solicitudes-correo/', include('solicitud_correo.urls')),
    path('solicitudes-vpn/', include('solicitud_vpn.urls')),
    path('solicitudes-codigo/', include('solicitud_codigo.urls')),
    path('api/v1/php/', peticion_php, name='peticion_php'),
]

handler404 = 'core.views.errors.handler404'
handler403 = 'core.views.errors.handler403'
handler500 = 'core.views.errors.handler500'

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
