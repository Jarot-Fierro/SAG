from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models.unidad_organizacional import UnidadOrganizacional


@login_required
def unidad_organizacional_grafico(request):
    unidades_todas = UnidadOrganizacional.objects.filter(is_active=True).prefetch_related('funcionarios__user').all()
    
    # Identificamos las unidades principales (raíces de cada card)
    # Una unidad es raíz si no tiene padre O si es unidad_principal=True
    raices = [u for u in unidades_todas if not u.padre or u.unidad_principal]
    
    # Para cada raíz, recolectamos sus descendientes (sin cruzar otras unidades principales)
    jerarquias = []
    for raiz in raices:
        sub_unidades = []
        def buscar_descendientes(actual):
            sub_unidades.append(actual)
            # Buscamos hijos que NO sean marcados como unidad_principal
            hijos = [u for u in unidades_todas if u.padre_id == actual.id and not u.unidad_principal]
            for hijo in hijos:
                buscar_descendientes(hijo)
        
        buscar_descendientes(raiz)
        jerarquias.append({
            'raiz': raiz,
            'unidades': sub_unidades
        })
    
    return render(request, 'core/unidad_organizacional_grafico.html', {
        'jerarquias': jerarquias,
    })
