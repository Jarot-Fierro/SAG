from django.urls import path

from .views import catalogo, computador, pdfs

app_name = 'gestion_tic'

urlpatterns = [
    # Computadores
    path('equipo/computador/', computador.ComputadorListView.as_view(), name='computador_list'),
    path('equipo/computador/nuevo/', computador.ComputadorCreateView.as_view(), name='computador_create'),
    path('equipo/computador/editar/<int:pk>/', computador.ComputadorUpdateView.as_view(), name='computador_update'),
    path('equipo/computador/desactivar/<int:pk>/', computador.computador_desactivar, name='computador_delete'),
    path('equipo/computador/pdf/<int:pk>/', pdfs.generar_pdf_computador, name='computador_pdf'),

    # Marca
    path('catalogo/marca/', catalogo.MarcaListView.as_view(), name='marca_list'),
    path('catalogo/marca/nuevo/', catalogo.MarcaCreateView.as_view(), name='marca_create'),
    path('catalogo/marca/editar/<int:pk>/', catalogo.MarcaUpdateView.as_view(), name='marca_update'),
    path('catalogo/marca/desactivar/<int:pk>/', catalogo.marca_desactivar, name='marca_delete'),

    # Categoria
    path('catalogo/categoria/', catalogo.CategoriaListView.as_view(), name='categoria_list'),
    path('catalogo/categoria/nuevo/', catalogo.CategoriaCreateView.as_view(), name='categoria_create'),
    path('catalogo/categoria/editar/<int:pk>/', catalogo.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('catalogo/categoria/desactivar/<int:pk>/', catalogo.categoria_desactivar, name='categoria_delete'),

    # Ips
    path('catalogo/ips/', catalogo.IpsListView.as_view(), name='ips_list'),
    path('catalogo/ips/nuevo/', catalogo.IpsCreateView.as_view(), name='ips_create'),
    path('catalogo/ips/editar/<int:pk>/', catalogo.IpsUpdateView.as_view(), name='ips_update'),
    path('catalogo/ips/desactivar/<int:pk>/', catalogo.ips_desactivar, name='ips_delete'),

    # JefeTic
    path('catalogo/jefetic/', catalogo.JefeTicListView.as_view(), name='jefetic_list'),
    path('catalogo/jefetic/nuevo/', catalogo.JefeTicCreateView.as_view(), name='jefetic_create'),
    path('catalogo/jefetic/editar/<int:pk>/', catalogo.JefeTicUpdateView.as_view(), name='jefetic_update'),
    path('catalogo/jefetic/desactivar/<int:pk>/', catalogo.jefetic_desactivar, name='jefetic_delete'),

    # LicenciaOs
    path('catalogo/licenciaos/', catalogo.LicenciaOsListView.as_view(), name='licenciaos_list'),
    path('catalogo/licenciaos/nuevo/', catalogo.LicenciaOsCreateView.as_view(), name='licenciaos_create'),
    path('catalogo/licenciaos/editar/<int:pk>/', catalogo.LicenciaOsUpdateView.as_view(), name='licenciaos_update'),
    path('catalogo/licenciaos/desactivar/<int:pk>/', catalogo.licenciaos_desactivar, name='licenciaos_delete'),

    # MicrosoftOffice
    path('catalogo/microsoftoffice/', catalogo.MicrosoftOfficeListView.as_view(), name='microsoftoffice_list'),
    path('catalogo/microsoftoffice/nuevo/', catalogo.MicrosoftOfficeCreateView.as_view(),
         name='microsoftoffice_create'),
    path('catalogo/microsoftoffice/editar/<int:pk>/', catalogo.MicrosoftOfficeUpdateView.as_view(),
         name='microsoftoffice_update'),
    path('catalogo/microsoftoffice/desactivar/<int:pk>/', catalogo.microsoftoffice_desactivar,
         name='microsoftoffice_delete'),

    # Modelo
    path('catalogo/modelo/', catalogo.ModeloListView.as_view(), name='modelo_list'),
    path('catalogo/modelo/nuevo/', catalogo.ModeloCreateView.as_view(), name='modelo_create'),
    path('catalogo/modelo/editar/<int:pk>/', catalogo.ModeloUpdateView.as_view(), name='modelo_update'),
    path('catalogo/modelo/desactivar/<int:pk>/', catalogo.modelo_desactivar, name='modelo_delete'),

    # Propietario
    path('catalogo/propietario/', catalogo.PropietarioListView.as_view(), name='propietario_list'),
    path('catalogo/propietario/nuevo/', catalogo.PropietarioCreateView.as_view(), name='propietario_create'),
    path('catalogo/propietario/editar/<int:pk>/', catalogo.PropietarioUpdateView.as_view(), name='propietario_update'),
    path('catalogo/propietario/desactivar/<int:pk>/', catalogo.propietario_desactivar, name='propietario_delete'),

    # PuestoTrabajo
    path('catalogo/puestotrabajo/', catalogo.PuestoTrabajoListView.as_view(), name='puestotrabajo_list'),
    path('catalogo/puestotrabajo/nuevo/', catalogo.PuestoTrabajoCreateView.as_view(), name='puestotrabajo_create'),
    path('catalogo/puestotrabajo/editar/<int:pk>/', catalogo.PuestoTrabajoUpdateView.as_view(),
         name='puestotrabajo_update'),
    path('catalogo/puestotrabajo/desactivar/<int:pk>/', catalogo.puestotrabajo_desactivar, name='puestotrabajo_delete'),

    # SistemaOperativo
    path('catalogo/sistemaoperativo/', catalogo.SistemaOperativoListView.as_view(), name='sistemaoperativo_list'),
    path('catalogo/sistemaoperativo/nuevo/', catalogo.SistemaOperativoCreateView.as_view(),
         name='sistemaoperativo_create'),
    path('catalogo/sistemaoperativo/editar/<int:pk>/', catalogo.SistemaOperativoUpdateView.as_view(),
         name='sistemaoperativo_update'),
    path('catalogo/sistemaoperativo/desactivar/<int:pk>/', catalogo.sistemaoperativo_desactivar,
         name='sistemaoperativo_delete'),

    # SubCategoria
    path('catalogo/subcategoria/', catalogo.SubCategoriaListView.as_view(), name='subcategoria_list'),
    path('catalogo/subcategoria/nuevo/', catalogo.SubCategoriaCreateView.as_view(), name='subcategoria_create'),
    path('catalogo/subcategoria/editar/<int:pk>/', catalogo.SubCategoriaUpdateView.as_view(),
         name='subcategoria_update'),
    path('catalogo/subcategoria/desactivar/<int:pk>/', catalogo.subcategoria_desactivar, name='subcategoria_delete'),

    # TipoCelular
    path('catalogo/tipocelular/', catalogo.TipoCelularListView.as_view(), name='tipocelular_list'),
    path('catalogo/tipocelular/nuevo/', catalogo.TipoCelularCreateView.as_view(), name='tipocelular_create'),
    path('catalogo/tipocelular/editar/<int:pk>/', catalogo.TipoCelularUpdateView.as_view(), name='tipocelular_update'),
    path('catalogo/tipocelular/desactivar/<int:pk>/', catalogo.tipocelular_desactivar, name='tipocelular_delete'),

    # TipoComputador
    path('catalogo/tipocomputador/', catalogo.TipoComputadorListView.as_view(), name='tipocomputador_list'),
    path('catalogo/tipocomputador/nuevo/', catalogo.TipoComputadorCreateView.as_view(), name='tipocomputador_create'),
    path('catalogo/tipocomputador/editar/<int:pk>/', catalogo.TipoComputadorUpdateView.as_view(),
         name='tipocomputador_update'),
    path('catalogo/tipocomputador/desactivar/<int:pk>/', catalogo.tipocomputador_desactivar,
         name='tipocomputador_delete'),

    # TipoImpresora
    path('catalogo/tipoimpresora/', catalogo.TipoImpresoraListView.as_view(), name='tipoimpresora_list'),
    path('catalogo/tipoimpresora/nuevo/', catalogo.TipoImpresoraCreateView.as_view(), name='tipoimpresora_create'),
    path('catalogo/tipoimpresora/editar/<int:pk>/', catalogo.TipoImpresoraUpdateView.as_view(),
         name='tipoimpresora_update'),
    path('catalogo/tipoimpresora/desactivar/<int:pk>/', catalogo.tipoimpresora_desactivar, name='tipoimpresora_delete'),

    # Toner
    path('catalogo/toner/', catalogo.TonerListView.as_view(), name='toner_list'),
    path('catalogo/toner/nuevo/', catalogo.TonerCreateView.as_view(), name='toner_create'),
    path('catalogo/toner/editar/<int:pk>/', catalogo.TonerUpdateView.as_view(), name='toner_update'),
    path('catalogo/toner/desactivar/<int:pk>/', catalogo.toner_desactivar, name='toner_delete'),

    # Contrato
    path('catalogo/contrato/', catalogo.ContratoListView.as_view(), name='contrato_list'),
    path('catalogo/contrato/nuevo/', catalogo.ContratoCreateView.as_view(), name='contrato_create'),
    path('catalogo/contrato/editar/<int:pk>/', catalogo.ContratoUpdateView.as_view(), name='contrato_update'),
    path('catalogo/contrato/desactivar/<int:pk>/', catalogo.contrato_desactivar, name='contrato_delete'),
]
