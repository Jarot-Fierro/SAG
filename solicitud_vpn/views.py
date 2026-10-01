import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from core.models.funcionario import Funcionario
from solicitud_vpn.forms import (
    SolicitudVPNForm,
    BeneficiarioVPNFormSet,
    SolicitudAccesoFormSet,
    GestionTICSolicitudForm,
    FiltroSolicitudVPNForm,
    PerfilVPNForm,
)
from solicitud_vpn.models import SolicitudVPN, AccesoVPN, PerfilVPN
from solicitud_vpn.permissions import user_is_vpn_gestor, VPNRequiredMixin
from solicitud_vpn.utils import obtener_datos_tecnico_solicitante

logger = logging.getLogger(__name__)

MODULE_NAME = 'Solicitudes de Acceso VPN'


class SolicitudVPNMisSolicitudesListView(LoginRequiredMixin, ListView):
    """
    Bandeja 'Mis solicitudes': Muestra las solicitudes creadas por el usuario autenticado.
    """
    model = SolicitudVPN
    template_name = 'solicitud_vpn/mis_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 15

    def get_queryset(self):
        queryset = SolicitudVPN.objects.filter(is_active=True).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante'
        ).prefetch_related('beneficiarios', 'accesos')

        # Si no es superuser ni gestor VPN, ve sus propias solicitudes
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario_solicitante=self.request.user)

        # Filtros
        form = FiltroSolicitudVPNForm(self.request.GET)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            accion = form.cleaned_data.get('accion')
            termino = form.cleaned_data.get('beneficiario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if accion:
                queryset = queryset.filter(accion=accion)
            if termino:
                queryset = queryset.filter(
                    Q(beneficiarios__rut__icontains=termino) |
                    Q(beneficiarios__nombres__icontains=termino) |
                    Q(beneficiarios__apellidos__icontains=termino) |
                    Q(beneficiarios__nombre_completo__icontains=termino)
                ).distinct()

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mis Solicitudes de Acceso VPN'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudVPNForm(self.request.GET)
        context['es_gestor_vpn'] = user_is_vpn_gestor(self.request.user)

        # Contadores rápidos del usuario
        qs_user = SolicitudVPN.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            qs_user = qs_user.filter(usuario_solicitante=self.request.user)

        context['total_solicitudes'] = qs_user.count()
        context['total_pendientes'] = qs_user.filter(estado='PENDIENTE').count()
        context['total_en_revision'] = qs_user.filter(estado='EN_REVISION').count()
        context['total_enviadas_econecta'] = qs_user.filter(estado='ENVIADO_ECONECTA').count()
        context['total_completadas'] = qs_user.filter(estado='COMPLETADO').count()
        context['total_rechazadas'] = qs_user.filter(estado='RECHAZADO').count()
        return context


class SolicitudVPNCreateView(LoginRequiredMixin, View):
    """
    Creación de una nueva solicitud de VPN con FormSets de Beneficiarios y Accesos.
    Maneja conjuntamente:
      - form
      - beneficiarios_formset
      - accesos_formset
    Validando los tres antes de guardar de manera atómica.
    """
    template_name = 'solicitud_vpn/form_solicitud.html'

    def get_funcionarios_disponibles(self, request):
        func_qs = Funcionario.objects.filter(is_active=True).order_by('nombres', 'apellidos')
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            func_qs = func_qs.filter(establecimiento=request.user.establecimiento)
        return func_qs

    def get_context_data(self, request, form=None, beneficiarios_formset=None, accesos_formset=None):
        if form is None:
            form = SolicitudVPNForm(request=request)
        if beneficiarios_formset is None:
            beneficiarios_formset = BeneficiarioVPNFormSet(prefix='beneficiarios')
        if accesos_formset is None:
            accesos_formset = SolicitudAccesoFormSet(prefix='accesos')

        return {
            'form': form,
            'beneficiarios_formset': beneficiarios_formset,
            'accesos_formset': accesos_formset,
            'title': 'Generar Requerimiento de Acceso VPN',
            'module_name': MODULE_NAME,
            'es_gestor_vpn': user_is_vpn_gestor(request.user),
            'funcionarios_disponibles': self.get_funcionarios_disponibles(request),
            'accesos_disponibles': AccesoVPN.objects.filter(is_active=True).order_by('plataforma', 'ip'),
            'establecimiento_usuario': getattr(request.user, 'establecimiento', None),
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = SolicitudVPNForm(request.POST, request=request)
        beneficiarios_formset = BeneficiarioVPNFormSet(request.POST, prefix='beneficiarios')
        accesos_formset = SolicitudAccesoFormSet(request.POST, prefix='accesos')

        es_borrador = request.POST.get('guardar_borrador') == '1'

        is_form_valid = form.is_valid()
        is_ben_valid = beneficiarios_formset.is_valid()
        is_acc_valid = accesos_formset.is_valid()

        if is_form_valid and is_ben_valid and is_acc_valid:
            nuevo_estado = 'BORRADOR' if es_borrador else 'PENDIENTE'

            with transaction.atomic():
                solicitud = form.save(commit=False)
                solicitud.usuario_solicitante = request.user
                solicitud.created_by = request.user
                solicitud.establecimiento = getattr(request.user, 'establecimiento', None)
                solicitud.estado = nuevo_estado
                solicitud.fecha_solicitud = timezone.now()
                solicitud.save()

                # Guardar beneficiarios
                beneficiarios_formset.instance = solicitud
                beneficiarios = beneficiarios_formset.save(commit=False)
                for ben in beneficiarios:
                    ben.solicitud = solicitud
                    ben.created_by = request.user
                    if not ben.establecimiento and solicitud.establecimiento:
                        ben.establecimiento = solicitud.establecimiento.nombre
                    ben.save()

                for del_obj in beneficiarios_formset.deleted_objects:
                    del_obj.delete()

                # Guardar accesos seleccionados (ManyToMany)
                accesos_seleccionados = []
                for acc_form in accesos_formset:
                    if acc_form.cleaned_data and not acc_form.cleaned_data.get('DELETE', False):
                        acc = acc_form.cleaned_data.get('acceso')
                        if acc:
                            accesos_seleccionados.append(acc)

                solicitud.accesos.set(accesos_seleccionados)

            if es_borrador:
                messages.info(request, f"Solicitud {solicitud.numero_solicitud} guardada en estado Borrador.")
            else:
                messages.success(
                    request,
                    f"Solicitud {solicitud.numero_solicitud} generada con éxito y enviada a la Bandeja TIC."
                )

            return redirect('solicitud_vpn:mis_solicitudes')

        messages.error(request, "Por favor corrija los errores en el formulario antes de enviar.")
        context = self.get_context_data(
            request,
            form=form,
            beneficiarios_formset=beneficiarios_formset,
            accesos_formset=accesos_formset
        )
        return render(request, self.template_name, context)


class SolicitudVPNBandejaTICListView(VPNRequiredMixin, ListView):
    """
    Bandeja TIC: Muestra las solicitudes de acceso VPN de todos los establecimientos
    del Servicio de Salud Arauco para su revisión y preparación de requerimiento en eConecta.
    """
    model = SolicitudVPN
    template_name = 'solicitud_vpn/bandeja_tic.html'
    context_object_name = 'solicitudes'
    paginate_by = 20

    def get_queryset(self):
        queryset = SolicitudVPN.objects.filter(is_active=True).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante', 'usuario_revision'
        ).prefetch_related('beneficiarios', 'accesos')

        form = FiltroSolicitudVPNForm(self.request.GET)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            establecimiento = form.cleaned_data.get('establecimiento')
            accion = form.cleaned_data.get('accion')
            termino = form.cleaned_data.get('beneficiario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if establecimiento:
                queryset = queryset.filter(establecimiento=establecimiento)
            if accion:
                queryset = queryset.filter(accion=accion)
            if termino:
                queryset = queryset.filter(
                    Q(beneficiarios__rut__icontains=termino) |
                    Q(beneficiarios__nombres__icontains=termino) |
                    Q(beneficiarios__apellidos__icontains=termino) |
                    Q(beneficiarios__nombre_completo__icontains=termino)
                ).distinct()

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bandeja de Gestión VPN - Informática / TIC'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudVPNForm(self.request.GET)
        context['es_gestor_vpn'] = True

        # Contadores / KPIs TIC
        qs_all = SolicitudVPN.objects.filter(is_active=True)
        context['total_pendientes'] = qs_all.filter(estado='PENDIENTE').count()
        context['total_en_revision'] = qs_all.filter(estado='EN_REVISION').count()
        context['total_enviadas_econecta'] = qs_all.filter(estado='ENVIADO_ECONECTA').count()
        context['total_completadas'] = qs_all.filter(estado='COMPLETADO').count()
        context['total_general'] = qs_all.count()
        return context


class SolicitudVPNDetalleView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle y revisión TIC de la solicitud VPN.
    Muestra los datos del solicitante/técnico en texto plano y tablas estructuradas
    de beneficiarios y accesos para facilitar la copia de información a eConecta.
    """
    model = SolicitudVPN
    template_name = 'solicitud_vpn/detalle_solicitud.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        queryset = SolicitudVPN.objects.all().select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante', 'usuario_revision'
        ).prefetch_related(
            'beneficiarios', 'beneficiarios__funcionario', 'accesos'
        )

        # Si no es superuser ni gestor VPN, solo puede ver sus propias solicitudes
        if not self.request.user.is_superuser and not user_is_vpn_gestor(self.request.user):
            queryset = queryset.filter(usuario_solicitante=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.object
        context['title'] = f"Detalle de Solicitud VPN {solicitud.numero_solicitud or f'#{solicitud.id}'}"
        context['module_name'] = MODULE_NAME
        context['es_gestor_vpn'] = user_is_vpn_gestor(self.request.user)
        context['gestion_form'] = GestionTICSolicitudForm(initial={
            'estado': solicitud.estado,
            'ticket_econecta': solicitud.ticket_econecta or '',
            'observacion_revision': solicitud.observacion_revision or ''
        })

        # Construir resumen en texto plano formateado para copiar rápidamente a eConecta
        econecta_text_lines = []
        econecta_text_lines.append("=== DATOS DEL SOLICITANTE / REFERENTE INFORMÁTICO ===")
        econecta_text_lines.append(f"Nombre Completo: {solicitud.tecnico_nombre or '-'}")
        econecta_text_lines.append(f"RUT: {solicitud.tecnico_rut or '-'}")
        econecta_text_lines.append(f"Establecimiento: {solicitud.tecnico_establecimiento or (solicitud.establecimiento.nombre if solicitud.establecimiento else '-')}")
        econecta_text_lines.append(f"Teléfono: {solicitud.tecnico_telefono or '-'}")
        econecta_text_lines.append(f"Cargo: {solicitud.tecnico_cargo or '-'}")
        econecta_text_lines.append(f"Fecha Requerimiento: {solicitud.tecnico_fecha or timezone.now().date()}")
        econecta_text_lines.append(f"Email: {solicitud.tecnico_email or '-'}")
        econecta_text_lines.append(f"Es Proveedor / Tercero: {'SÍ' if solicitud.es_proveedor else 'NO'}")
        econecta_text_lines.append("")
        econecta_text_lines.append("=== PARÁMETROS VPN ===")
        econecta_text_lines.append(f"Acción Solicitada: {solicitud.get_accion_display()}")
        econecta_text_lines.append(f"Grupo VPN: {solicitud.grupo_vpn or 'N/A'}")
        econecta_text_lines.append(f"Fecha Expiración: {solicitud.fecha_expiracion or 'Indefinida / No especificada'}")
        econecta_text_lines.append(f"Time Out VPN: {solicitud.timeout_vpn or '1 hora'}")
        if solicitud.observacion:
            econecta_text_lines.append(f"Observaciones: {solicitud.observacion}")
        econecta_text_lines.append("")
        econecta_text_lines.append(f"=== BENEFICIARIOS ({solicitud.beneficiarios.count()}) ===")

        for idx, ben in enumerate(solicitud.beneficiarios.all(), 1):
            econecta_text_lines.append(f"[{idx}] Nombre: {ben.get_nombre_completo()} | RUT: {ben.rut or '-'} | Cargo: {ben.cargo or '-'} | Establecimiento: {ben.establecimiento or '-'} | Email: {ben.email or '-'} | Teléfono: {ben.telefono or '-'}")

        econecta_text_lines.append("")
        econecta_text_lines.append(f"=== ACCESOS VPN SOLICITADOS ({solicitud.accesos.count()}) ===")
        accesos = solicitud.accesos.all()
        if accesos.exists():
            for a_idx, acc in enumerate(accesos, 1):
                econecta_text_lines.append(
                    f"  [{a_idx}] Sistema: {acc.plataforma} | IP / Dirección: {acc.ip}"
                )
        else:
            econecta_text_lines.append("  (Sin accesos específicos registrados)")

        context['texto_econecta_completo'] = "\n".join(econecta_text_lines)
        return context


class SolicitudVPNCambiarEstadoView(VPNRequiredMixin, View):
    """
    Endpoint para cambiar el estado de la solicitud VPN, registrar el ticket eConecta y observaciones.
    """
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudVPN, pk=pk)
        form = GestionTICSolicitudForm(request.POST)

        if form.is_valid():
            nuevo_estado = form.cleaned_data['estado']
            ticket_econecta = form.cleaned_data.get('ticket_econecta', '')
            observacion = form.cleaned_data.get('observacion_revision', '')

            solicitud.estado = nuevo_estado
            solicitud.ticket_econecta = ticket_econecta
            solicitud.observacion_revision = observacion
            solicitud.usuario_revision = request.user
            solicitud.updated_by = request.user

            now = timezone.now()
            if nuevo_estado == 'EN_REVISION' and not solicitud.fecha_revision:
                solicitud.fecha_revision = now
            elif nuevo_estado == 'ENVIADO_ECONECTA':
                if not solicitud.fecha_revision:
                    solicitud.fecha_revision = now
                solicitud.fecha_envio_econecta = now
            elif nuevo_estado in ['COMPLETADO', 'RECHAZADO']:
                if not solicitud.fecha_revision:
                    solicitud.fecha_revision = now
                solicitud.fecha_finalizacion = now

            solicitud.save()

            messages.success(
                request,
                f"Estado de la solicitud {solicitud.numero_solicitud} actualizado a '{solicitud.get_estado_display()}'."
            )
        else:
            messages.error(request, "Error al actualizar el estado de la solicitud. Verifique los datos.")

        return redirect('solicitud_vpn:detalle', pk=solicitud.pk)


class PerfilVPNView(LoginRequiredMixin, View):
    """
    Vista para ver y actualizar el perfil de gestión VPN y datos de técnico referente del usuario conectado.
    """
    template_name = 'solicitud_vpn/perfil_vpn.html'

    def get(self, request):
        perfil, _ = PerfilVPN.objects.get_or_create(usuario=request.user)
        # Si está recién creado o vacío, autocompletar con datos de funcionario/user
        if not perfil.nombre_completo:
            datos = obtener_datos_tecnico_solicitante(request.user)
            perfil.nombre_completo = datos['nombre_completo']
            perfil.rut = datos['rut']
            perfil.establecimiento = datos['establecimiento']
            perfil.telefono = datos['telefono']
            perfil.cargo = datos['cargo']
            perfil.email = datos['email']
            perfil.save()

        form = PerfilVPNForm(instance=perfil)
        return render(request, self.template_name, {
            'form': form,
            'perfil': perfil,
            'title': 'Mi Perfil de Referente VPN',
            'module_name': MODULE_NAME,
            'es_gestor_vpn': user_is_vpn_gestor(request.user),
        })

    def post(self, request):
        perfil, _ = PerfilVPN.objects.get_or_create(usuario=request.user)
        form = PerfilVPNForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de perfil VPN actualizados con éxito.")
            return redirect('solicitud_vpn:perfil')
        return render(request, self.template_name, {
            'form': form,
            'perfil': perfil,
            'title': 'Mi Perfil de Referente VPN',
            'module_name': MODULE_NAME,
            'es_gestor_vpn': user_is_vpn_gestor(request.user),
        })


class FuncionarioDataAPIView(LoginRequiredMixin, View):
    """
    API JSON que retorna los datos de un Funcionario para autocompletar filas de beneficiarios.
    """
    def get(self, request, pk):
        try:
            f = Funcionario.objects.get(pk=pk, is_active=True)
            data = {
                'id': f.id,
                'rut': f.rut or '',
                'nombres': f.nombres or '',
                'apellidos': f.apellidos or '',
                'nombre_completo': f.nombre or f"{f.nombres or ''} {f.apellidos or ''}".strip(),
                'establecimiento': f.establecimiento.nombre if f.establecimiento else '',
                'cargo': f.cargo or '',
                'email': f.email or '',
                'telefono': '',
                'fecha': timezone.now().date().strftime('%Y-%m-%d')
            }
            return JsonResponse({'status': 'ok', 'data': data})
        except Funcionario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Funcionario no encontrado'}, status=404)
