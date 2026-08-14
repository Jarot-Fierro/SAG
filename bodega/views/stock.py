from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from bodega.forms.forms import (
    FormStock, FormEntradaStock, FormSalidaStock,
    FormAjusteStock, FormTransferenciaStock
)
from bodega.models import Bodega
from bodega.models.movimientos import MovimientoInventario
from bodega.models.stock import Stock
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView

MODULE_NAME = 'Stock'


class StockListView(StandardListView):
    model = Stock
    template_name = "bodega/list_stock.html"
    title = "Stock"
    search_fields = ['producto__nombre', 'bodega__nombre']
    list_url_name = "bodega:stock_list"
    create_url_name = "bodega:stock_create"
    update_url_name = "bodega:stock_update"
    delete_url_name = "bodega:stock_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related('bodega', 'producto')
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            queryset = queryset.filter(bodega_id=bodega_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()

        # URLs para operaciones de stock (JS)
        context['url_stock_operacion'] = reverse('bodega:stock_entrada', kwargs={'pk': 0}).replace('0',
                                                                                                   '__pk__').replace(
            'entrada', '__type__')
        context['url_api_bodegas_destino'] = reverse('bodega:api_get_bodegas_destino', kwargs={'pk': 0}).replace('0',
                                                                                                                 '__pk__')

        return context


class StockCreateView(StandardCreateView):
    model = Stock
    form_class = FormStock
    template_name = 'bodega/form_stock.html'
    title = 'Nuevo Stock'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['bodega'] = self.request.GET.get('bodega')
        return kwargs

    def get_success_url(self):
        bodega_id = self.request.GET.get('bodega')
        return f"{reverse('bodega:stock_list')}?bodega={bodega_id}"

    def form_valid(self, form):
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            form.instance.bodega = get_object_or_404(Bodega, pk=bodega_id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context


class StocksUpdateView(StandardUpdateView):
    model = Stock
    form_class = FormStock
    template_name = 'bodega/form_stock.html'
    title = 'Editar Stock'
    module_name = MODULE_NAME

    def get_success_url(self):
        bodega_id = self.request.GET.get('bodega')
        return f"{reverse('bodega:stock_list')}?bodega={bodega_id}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['bodega'] = self.request.GET.get('bodega')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context


@transaction.atomic
def stock_entrada(request, pk):
    stock = get_object_or_404(Stock.objects.select_for_update(), pk=pk)
    form = FormEntradaStock(request.POST)
    if form.is_valid():
        cantidad = form.cleaned_data['cantidad']
        observacion = form.cleaned_data['observacion']

        stock.stock_actual += cantidad
        stock.save()

        MovimientoInventario.objects.create(
            inventario=stock,
            tipo=MovimientoInventario.ENTRADA,
            cantidad=cantidad,
            usuario=request.user,
            observacion=observacion,
            establecimiento=request.user.establecimiento,
            created_by=request.user
        )
        messages.success(request, "Stock ingresado correctamente.")
    else:
        messages.error(request, "Error al procesar la entrada de stock.")
    return redirect(f"{reverse('bodega:stock_list')}?bodega={stock.bodega.pk}")


@transaction.atomic
def stock_salida(request, pk):
    stock = get_object_or_404(Stock.objects.select_for_update(), pk=pk)
    form = FormSalidaStock(request.POST)
    if form.is_valid():
        cantidad = form.cleaned_data['cantidad']
        observacion = form.cleaned_data['observacion']

        if stock.stock_actual < cantidad:
            messages.error(request, "No hay stock suficiente para realizar esta operación.")
        else:
            stock.stock_actual -= cantidad
            stock.save()

            MovimientoInventario.objects.create(
                inventario=stock,
                tipo=MovimientoInventario.SALIDA,
                cantidad=cantidad,
                usuario=request.user,
                observacion=observacion,
                establecimiento=request.user.establecimiento,
                created_by=request.user
            )
            messages.success(request, "Salida registrada correctamente.")
    else:
        messages.error(request, "Error al procesar la salida de stock.")
    return redirect(f"{reverse('bodega:stock_list')}?bodega={stock.bodega.pk}")


@transaction.atomic
def stock_ajuste(request, pk):
    stock = get_object_or_404(Stock.objects.select_for_update(), pk=pk)
    form = FormAjusteStock(request.POST)
    if form.is_valid():
        tipo_ajuste = form.cleaned_data['tipo_ajuste']
        cantidad = form.cleaned_data['cantidad']
        observacion = form.cleaned_data['observacion']

        if tipo_ajuste == 'AUMENTAR':
            stock.stock_actual += cantidad
            stock.save()
            MovimientoInventario.objects.create(
                inventario=stock,
                tipo=MovimientoInventario.AJUSTE,
                cantidad=cantidad,
                usuario=request.user,
                observacion=f"Aumento: {observacion}",
                establecimiento=request.user.establecimiento,
                created_by=request.user
            )
            messages.success(request, "Ajuste de stock realizado correctamente.")
        else:  # DISMINUIR
            if stock.stock_actual < cantidad:
                messages.error(request, "No hay stock suficiente para realizar esta operación.")
            else:
                stock.stock_actual -= cantidad
                stock.save()
                MovimientoInventario.objects.create(
                    inventario=stock,
                    tipo=MovimientoInventario.AJUSTE,
                    cantidad=cantidad,
                    usuario=request.user,
                    observacion=f"Disminución: {observacion}",
                    establecimiento=request.user.establecimiento,
                    created_by=request.user
                )
                messages.success(request, "Ajuste de stock realizado correctamente.")
    else:
        messages.error(request, "Error al procesar el ajuste de stock.")
    return redirect(f"{reverse('bodega:stock_list')}?bodega={stock.bodega.pk}")


@transaction.atomic
def stock_transferencia(request, pk):
    stock_origen = get_object_or_404(Stock.objects.select_for_update(), pk=pk)
    form = FormTransferenciaStock(request.POST, stock=stock_origen, user=request.user)
    if form.is_valid():
        bodega_destino = form.cleaned_data['bodega_destino']
        cantidad = form.cleaned_data['cantidad']
        observacion = form.cleaned_data['observacion']

        if stock_origen.stock_actual < cantidad:
            messages.error(request, "No hay stock suficiente para realizar esta operación.")
        else:
            # Descontar origen
            stock_origen.stock_actual -= cantidad
            stock_origen.save()

            # Registrar movimiento origen
            MovimientoInventario.objects.create(
                inventario=stock_origen,
                tipo=MovimientoInventario.TRANSFERENCIA,
                cantidad=cantidad,
                usuario=request.user,
                observacion=f"Transferencia hacia {bodega_destino.nombre}. {observacion}",
                establecimiento=request.user.establecimiento,
                created_by=request.user
            )

            # Incrementar destino
            stock_destino, created = Stock.objects.get_or_create(
                bodega=bodega_destino,
                producto=stock_origen.producto,
                defaults={
                    'stock_actual': 0,
                    'stock_minimo': 0,
                    'stock_maximo': 0,
                    'created_by': request.user
                }
            )
            # Volver a obtener con bloqueo si no fue creado
            if not created:
                stock_destino = Stock.objects.select_for_update().get(pk=stock_destino.pk)

            stock_destino.stock_actual += cantidad
            stock_destino.save()

            # Registrar movimiento destino
            MovimientoInventario.objects.create(
                inventario=stock_destino,
                tipo=MovimientoInventario.TRANSFERENCIA,
                cantidad=cantidad,
                usuario=request.user,
                observacion=f"Transferencia desde {stock_origen.bodega.nombre}. {observacion}",
                establecimiento=request.user.establecimiento,
                created_by=request.user
            )

            messages.success(request, "Transferencia realizada correctamente.")
    else:
        error_msg = form.errors.as_text()
        messages.error(request, f"Error al procesar la transferencia: {error_msg}")

    return redirect(f"{reverse('bodega:stock_list')}?bodega={stock_origen.bodega.pk}")


def api_get_bodegas_destino(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    user = request.user

    # Bodegas que NO son la origen
    qs = Bodega.objects.exclude(pk=stock.bodega.pk)

    # Bodegas que aceptan la categoría del producto
    qs = qs.filter(categorias=stock.producto.categoria)

    # Bodegas asignadas al usuario
    if hasattr(user, 'perfil_bodega'):
        qs = qs.filter(pk__in=user.perfil_bodega.bodegas.all())
    else:
        qs = qs.none()

    data = [{'id': b.id, 'nombre': b.nombre} for b in qs]
    return JsonResponse(data, safe=False)
