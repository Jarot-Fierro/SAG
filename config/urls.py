from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

from config import settings


def recibe_ip(request):
    print("\n" + "=" * 80)
    print("NUEVA VISITA")

    for clave, valor in request.META.items():
        print(f"{clave}: {valor}")

    print("=" * 80 + "\n")

    return HttpResponse("No eres Bienvenido")


urlpatterns = [
    path('admin/', admin.site.urls),
    path("select2/", include("django_select2.urls")),
    path('', include('core.urls')),
    path('agenda/', include('agenda_telefonica.urls')),
    path('soporte/', include('soporte.urls')),
    path('horos/', include('horos.urls')),
    path('gestion/', include('gestion_tic.urls')),
    path('bodega/', include('bodega.urls')),
    path('viaticos/', include('viaticos.urls')),
    path('recibe/', recibe_ip),
]

handler404 = 'core.views.errors.handler404'
handler403 = 'core.views.errors.handler403'
handler500 = 'core.views.errors.handler500'

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
