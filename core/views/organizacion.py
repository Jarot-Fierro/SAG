import unicodedata
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional


def normalizar_texto(texto):
    if not texto:
        return ""
    # Normalizar para eliminar acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = "".join([c for c in texto if unicodedata.category(c) != 'Mn'])
    return texto.upper()


@login_required
@require_GET
def buscar_funcionario_api(request):
    termino = request.GET.get('term', '')
    if not termino:
        return JsonResponse([], safe=False)

    # Limpiar el término de búsqueda si parece un RUT (quitar puntos y guion)
    termino_limpio = termino.replace('.', '').replace('-', '').upper()

    funcionarios = Funcionario.objects.filter(is_active=True)

    # Búsqueda estrictamente por RUT (usando el término limpio o el original)
    res = funcionarios.filter(
        Q(rut__iexact=termino) |
        Q(rut__iexact=termino_limpio) |
        Q(rut__icontains=termino_limpio)
    )[:5]

    data = []
    for f in res:
        data.append({
            'id': f.id,
            'rut': f.rut,
            'nombres': f.nombres,
            'apellidos': f.apellidos,
            'email': f.email,
            'establecimiento_id': f.establecimiento_id,
            'cargo': f.cargo,
            'profesion_id': f.profesion_id,
            'rol_organizacional_id': f.rol_organizacional_id,
            'unidad_organizacional_id': f.unidad_organizacional_id,
        })

    return JsonResponse(data, safe=False)


@login_required
def unidad_organizacional_grafico(request):
    unidades_todas = UnidadOrganizacional.objects.filter(is_active=True)

    # Identificamos las unidades principales (raíces de cada card)
    # Una unidad es raíz si no tiene padre O si es unidad_principal=True
    raices = unidades_todas.filter(Q(padre__isnull=True) | Q(unidad_principal=True))

    jerarquias = []
    for raiz in raices:
        # get_descendants(include_self=True) nos da todas las unidades bajo esta raíz
        # Filtramos para no incluir descendientes que sean a su vez raíces (unidad_principal)
        # para que no se dupliquen en diferentes gráficos si así se desea
        descendientes = raiz.get_descendants(include_self=True).filter(is_active=True)

        jerarquias.append({
            'raiz': raiz,
            'unidades': descendientes
        })

    return render(request, 'core/unidad_organizacional_grafico.html', {
        'jerarquias': jerarquias,
    })
