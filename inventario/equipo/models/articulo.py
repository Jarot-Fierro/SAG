# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from simple_history.models import HistoricalRecords
#
# from catalogo.models import Modelo, Marca, SubCategoria
# from core.standard.models import StandardModel
#
# ESTADO_EQUIPO = [
#     ('ASIGNADO', _('Asignado')),
#     ('EN STOCK', _('En bodega')),
# ]
#
# # Si ya tienes estos choices definidos, reutilízalos
# STATUS_SERIAL = (
#     ('EN STOCL', 'En stock'),
#     ('ASIGNADO', 'Asignado'),
#     ('EN REPARACION', 'En reparación'),
#     ('DADO DE BAJA', 'Dado de baja'),
#     ('EXTRAVIADO', 'Extraviado'),
# )
#
#
# class Articulo(StandardModel):
#     nombre = models.CharField(max_length=200, verbose_name='Nombre del Artículo')
#     cantidad = models.PositiveIntegerField(default=0, verbose_name='Cantidad en Stock')
#
#     estado_equipo = models.CharField(max_length=150, choices=ESTADO_EQUIPO, default='En stock')
#
#     descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
#     marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Marca')
#     modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Modelo')
#     subcategoria = models.ForeignKey(SubCategoria, on_delete=models.SET_NULL, null=True, blank=True,
#                                      verbose_name='Subcategoría')
#     con_series = models.BooleanField(default=False, verbose_name='¿Tiene serial?')
#     history = HistoricalRecords()
#
#     UPPERCASE_FIELDS = ['nombre', 'descripcion', ]
#
#     class Meta:
#         verbose_name = 'Artículo'
#         verbose_name_plural = 'Artículos'
#
#     def __str__(self):
#         return self.nombre
#
#
# class ArticleSerial(StandardModel):
#     article = models.ForeignKey('Articulo', on_delete=models.CASCADE, related_name='seriales', verbose_name='Artículo')
#     serial_number = models.CharField(max_length=255, unique=True, verbose_name='Código de Serie')
#     status = models.CharField(max_length=150, choices=STATUS_SERIAL, default='En stock',
#                               verbose_name='Estado del Serial')
#     observation = models.TextField(blank=True, null=True, verbose_name='Observación')
#
#     history = HistoricalRecords()
#
#     class Meta:
#         verbose_name = 'Serial de Artículo'
#         verbose_name_plural = 'Seriales de Artículos'
#         ordering = ['article__nombre', 'serial_number']
#         indexes = [
#             models.Index(fields=['serial_number']),
#             models.Index(fields=['article']),
#             models.Index(fields=['status']),
#         ]
#
#     def __str__(self):
#         return f'{self.article.nombre} - {self.serial_number}'
