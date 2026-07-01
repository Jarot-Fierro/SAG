from django.urls import path

from catalogo.views.categoria import *
from catalogo.views.categoria_inventario import *
from catalogo.views.contrato import *
from catalogo.views.ips import *
from catalogo.views.jefetic import *
from catalogo.views.licencia_os import *
from catalogo.views.marca import *
from catalogo.views.microsoft_office import *
from catalogo.views.modelo import *
from catalogo.views.propietario import *
from catalogo.views.puesto_trabajo import *
from catalogo.views.sistema_operativo import *
from catalogo.views.subcategoria import *
from catalogo.views.tipo_celular import *
from catalogo.views.tipo_computador import *
from catalogo.views.tipo_impresora import *
from catalogo.views.tipo_soporte import *
from catalogo.views.toner import *

urlpatterns = [
    # CATEGORÍAS
    path('lista-categorias/', CategoriaListView.as_view(), name='list_categorias'),
    path('detalle-categorias/<int:pk>/detalle/', CategoriaDetailView.as_view(), name='detail_categorias'),
    path('crear-categorias/', CategoriaCreateView.as_view(), name='create_categorias'),
    path('actualizar-categorias/<int:pk>/detalle/', CategoriaUpdateView.as_view(), name='update_categorias'),
    path('historial-categorias/', CategoriaHistoryListView.as_view(), name='historical_categorias'),

    # SUBCATEGORIAS
    path('lista-subcategorias/', SubCategoriaListView.as_view(), name='list_subcategorias'),
    path('detalle-subcategorias/<int:pk>/detalle/', SubCategoriaDetailView.as_view(), name='detail_subcategorias'),
    path('crear-subcategorias/', SubCategoriaCreateView.as_view(), name='create_subcategorias'),
    path('actualizar-subcategorias/<int:pk>/detalle/', SubCategoriaUpdateView.as_view(), name='update_subcategorias'),
    path('historial-subcategorias/', SubCategoriaHistoryListView.as_view(), name='historical_subcategorias'),

    # LICENCIA OS
    path('lista-licencia_os/', LicenciaOsListView.as_view(), name='list_licencia_os'),
    path('detalle-licencia_os/<int:pk>/detalle/', LicenciaOsDetailView.as_view(), name='detail_licencia_os'),
    path('crear-licencia_os/', LicenciaOsCreateView.as_view(), name='create_licencia_os'),
    path('actualizar-licencia_os/<int:pk>/detalle/', LicenciaOsUpdateView.as_view(), name='update_licencia_os'),
    path('historial-licencia_os/', LicenciaOsHistoryListView.as_view(), name='historical_licencia_os'),

    # MARCAS
    path('lista-marcas/', MarcaListView.as_view(), name='list_marcas'),
    path('detalle-marcas/<int:pk>/detalle/', MarcaDetailView.as_view(), name='detail_marcas'),
    path('crear-marcas/', MarcaCreateView.as_view(), name='create_marcas'),
    path('actualizar-marcas/<int:pk>/detalle/', MarcaUpdateView.as_view(), name='update_marcas'),
    path('historial-marcas/', MarcaHistoryListView.as_view(), name='historical_marcas'),

    # MICROSOFT OFFICE
    path('lista-microsoft_office/', MicrosoftOfficeListView.as_view(), name='list_microsoft_office'),
    path('detalle-microsoft_office/<int:pk>/detalle/', MicrosoftOfficeDetailView.as_view(),
         name='detail_microsoft_office'),
    path('crear-microsoft_office/', MicrosoftOfficeCreateView.as_view(), name='create_microsoft_office'),
    path('actualizar-microsoft_office/<int:pk>/detalle/', MicrosoftOfficeUpdateView.as_view(),
         name='update_microsoft_office'),
    path('historial-microsoft_office/', MicrosoftOfficeHistoryListView.as_view(), name='historical_microsoft_office'),

    # MODELOS
    path('lista-modelos/', ModeloListView.as_view(), name='list_modelos'),
    path('detalle-modelos/<int:pk>/detalle/', ModeloDetailView.as_view(), name='detail_modelos'),
    path('crear-modelos/', ModeloCreateView.as_view(), name='create_modelos'),
    path('actualizar-modelos/<int:pk>/detalle/', ModeloUpdateView.as_view(), name='update_modelos'),
    path('historial-modelos/', ModeloHistoryListView.as_view(), name='historical_modelos'),

    # PROPIETARIOS
    path('lista-propietarios/', PropietarioListView.as_view(), name='list_propietarios'),
    path('detalle-propietarios/<int:pk>/detalle/', PropietarioDetailView.as_view(), name='detail_propietarios'),
    path('crear-propietarios/', PropietarioCreateView.as_view(), name='create_propietarios'),
    path('actualizar-propietarios/<int:pk>/detalle/', PropietarioUpdateView.as_view(), name='update_propietarios'),
    path('historial-propietarios/', PropietarioHistoryListView.as_view(), name='historical_propietarios'),

    # SISTEMAS OPERATIVOS
    path('lista-sistemas-operativos/', SistemaOperativoListView.as_view(), name='list_sistemas_operativos'),
    path('detalle-sistemas-operativos/<int:pk>/detalle/', SistemaOperativoDetailView.as_view(),
         name='detail_sistemas_operativos'),
    path('crear-sistemas-operativos/', SistemaOperativoCreateView.as_view(), name='create_sistemas_operativos'),
    path('actualizar-sistemas-operativos/<int:pk>/detalle/', SistemaOperativoUpdateView.as_view(),
         name='update_sistemas_operativos'),
    path('historial-sistemas-operativos/', SistemaOperativoHistoryListView.as_view(),
         name='historical_sistemas_operativos'),

    # TIPO CELULAR
    path('lista-tipo-plan/', TipoCelularListView.as_view(), name='list_tipo_celular'),
    path('detalle-tipo-plan/<int:pk>/detalle/', TipoCelularDetailView.as_view(), name='detail_tipo_celular'),
    path('crear-tipo-plan/', TipoCelularCreateView.as_view(), name='create_tipo_celular'),
    path('actualizar-tipo-plan/<int:pk>/detalle/', TipoCelularUpdateView.as_view(), name='update_tipo_celular'),
    path('historial-tipo-plan/', TipoCelularHistoryListView.as_view(), name='historical_tipo_celular'),

    # TIPO COMPUTADOR
    path('lista-tipo-computador/', TipoComputadorListView.as_view(), name='list_tipo_computador'),
    path('detalle-tipo-computador/<int:pk>/detalle/', TipoComputadorDetailView.as_view(),
         name='detail_tipo_computador'),
    path('crear-tipo-computador/', TipoComputadorCreateView.as_view(), name='create_tipo_computador'),
    path('actualizar-tipo-computador/<int:pk>/detalle/', TipoComputadorUpdateView.as_view(),
         name='update_tipo_computador'),
    path('historial-tipo-computador/', TipoComputadorHistoryListView.as_view(), name='historical_tipo_computador'),

    # TIPO IMPRESORA
    path('lista-tipo-impresora/', TipoImpresoraListView.as_view(), name='list_tipo_impresora'),
    path('detalle-tipo-impresora/<int:pk>/detalle/', TipoImpresoraDetailView.as_view(), name='detail_tipo_impresora'),
    path('crear-tipo-impresora/', TipoImpresoraCreateView.as_view(), name='create_tipo_impresora'),
    path('actualizar-tipo-impresora/<int:pk>/detalle/', TipoImpresoraUpdateView.as_view(),
         name='update_tipo_impresora'),
    path('historial-tipo-impresora/', TipoImpresoraHistoryListView.as_view(), name='historical_tipo_impresora'),

    # TONER
    path('lista-toner/', TonerListView.as_view(), name='list_toner'),
    path('detalle-toner/<int:pk>/detalle/', TonerDetailView.as_view(), name='detail_toner'),
    path('crear-toner/', TonerCreateView.as_view(), name='create_toner'),
    path('actualizar-toner/<int:pk>/detalle/', TonerUpdateView.as_view(),
         name='update_toner'),
    path('historial-toner/', TonerHistoryListView.as_view(), name='historical_toner'),

    # CONTRATO
    path('lista-contrato/', ContratoListView.as_view(), name='list_contrato'),
    path('detalle-contrato/<int:pk>/detalle/', ContratoDetailView.as_view(), name='detail_contrato'),
    path('crear-contrato/', ContratoCreateView.as_view(), name='create_contrato'),
    path('actualizar-contrato/<int:pk>/detalle/', ContratoUpdateView.as_view(),
         name='update_contrato'),
    path('historial-contrato/', ContratoHistoryListView.as_view(), name='historical_contrato'),

    # JEFE TIC
    path('lista-jefetic/', JefeTicListView.as_view(), name='list_jefetic'),
    path('detalle-jefetic/<int:pk>/detalle/', JefeTicDetailView.as_view(), name='detail_jefetic'),
    path('crear-jefetic/', JefeTicCreateView.as_view(), name='create_jefetic'),
    path('actualizar-jefetic/<int:pk>/detalle/', JefeTicUpdateView.as_view(),
         name='update_jefetic'),
    path('historial-jefetic/', JefeTicHistoryListView.as_view(), name='historical_jefetic'),

    # TIPO SOPORTE
    path('lista-tipo_soporte/', TipoSoporteListView.as_view(), name='list_tipo_soporte'),
    path('detalle-tipo_soporte/<int:pk>/detalle/', TipoSoporteDetailView.as_view(), name='detail_tipo_soporte'),
    path('crear-tipo_soporte/', TipoSoporteCreateView.as_view(), name='create_tipo_soporte'),
    path('actualizar-tipo_soporte/<int:pk>/detalle/', TipoSoporteUpdateView.as_view(),
         name='update_tipo_soporte'),
    path('historial-tipo_soporte/', TipoSoporteHistoryListView.as_view(), name='historical_tipo_soporte'),

    # PUESTO TRABAJO
    path('lista-puesto_trabajo/', PuestoTrabajoListView.as_view(), name='list_puesto_trabajo'),
    path('detalle-puesto_trabajo/<int:pk>/detalle/', PuestoTrabajoDetailView.as_view(), name='detail_puesto_trabajo'),
    path('crear-puesto_trabajo/', PuestoTrabajoCreateView.as_view(), name='create_puesto_trabajo'),
    path('actualizar-puesto_trabajo/<int:pk>/detalle/', PuestoTrabajoUpdateView.as_view(),
         name='update_puesto_trabajo'),
    path('historial-puesto_trabajo/', PuestoTrabajoHistoryListView.as_view(), name='historical_puesto_trabajo'),

    # IPS
    path('lista-ips/', IpsListView.as_view(), name='list_ips'),
    path('detalle-ips/<int:pk>/detalle/', IpsDetailView.as_view(), name='detail_ips'),
    path('crear-ips/', IpsCreateView.as_view(), name='create_ips'),
    path('actualizar-ips/<int:pk>/detalle/', IpsUpdateView.as_view(),
         name='update_ips'),
    path('historial-ips/', IpsHistoryListView.as_view(), name='historical_ips'),

    # CATEGORÍAS INVENTARIO
    path('lista-categorias_inventario/', CategoriaInventarioListView.as_view(), name='list_categorias_inventario'),
    path('detalle-categorias_inventario/<int:pk>/detalle/', CategoriaInventarioDetailView.as_view(),
         name='detail_categorias_inventario'),
    path('crear-categorias_inventario/', CategoriaInventarioCreateView.as_view(), name='create_categorias_inventario'),
    path('actualizar-categorias_inventario/<int:pk>/detalle/', CategoriaInventarioUpdateView.as_view(),
         name='update_categorias_inventario'),
    path('historial-categorias_inventario/', CategoriaInventarioHistoryListView.as_view(),
         name='historical_categorias_inventario'),

]
