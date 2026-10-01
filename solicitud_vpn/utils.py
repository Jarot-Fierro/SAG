from django.utils import timezone


def obtener_departamento_principal(unidad):
    """
    Recorre la jerarquía padre/hijo de UnidadOrganizacional hacia arriba
    hasta encontrar el nivel marcado con es_departamento=True.
    Si no encuentra ninguno explícitamente marcado, devuelve la unidad raíz o la misma unidad.
    """
    if not unidad:
        return None

    actual = unidad
    ultimo_valido = unidad
    while actual:
        if getattr(actual, 'es_departamento', False):
            return actual
        ultimo_valido = actual
        if not getattr(actual, 'padre', None):
            break
        actual = actual.padre

    return ultimo_valido


def obtener_datos_tecnico_solicitante(user):
    """
    Obtiene los datos por defecto del solicitante / técnico a partir del usuario autenticado,
    su PerfilVPN o su Funcionario asociado.
    """
    datos = {
        'nombre_completo': '',
        'rut': '',
        'establecimiento': '',
        'telefono': '',
        'cargo': '',
        'email': '',
        'fecha': timezone.now().date(),
        'es_proveedor': False,
    }

    if not user or not user.is_authenticated:
        return datos

    # 1. Si tiene PerfilVPN con datos configurados
    if hasattr(user, 'perfil_vpn') and user.perfil_vpn:
        pv = user.perfil_vpn
        if pv.nombre_completo:
            datos['nombre_completo'] = pv.nombre_completo
        if pv.rut:
            datos['rut'] = pv.rut
        if pv.establecimiento:
            datos['establecimiento'] = pv.establecimiento
        if pv.telefono:
            datos['telefono'] = pv.telefono
        if pv.cargo:
            datos['cargo'] = pv.cargo
        if pv.email:
            datos['email'] = pv.email

    # 2. Si tiene Funcionario asociado
    if hasattr(user, 'funcionario') and user.funcionario:
        f = user.funcionario
        if not datos['nombre_completo']:
            datos['nombre_completo'] = f.nombre or f"{f.nombres or ''} {f.apellidos or ''}".strip()
        if not datos['rut'] and f.rut:
            datos['rut'] = f.rut
        if not datos['establecimiento'] and f.establecimiento:
            datos['establecimiento'] = f.establecimiento.nombre
        if not datos['cargo'] and f.cargo:
            datos['cargo'] = f.cargo
        if not datos['email'] and f.email:
            datos['email'] = f.email

    # 3. Datos del propio User
    if not datos['nombre_completo']:
        datos['nombre_completo'] = user.get_full_name() or user.username
    if not datos['email'] and user.email:
        datos['email'] = user.email
    if not datos['establecimiento'] and hasattr(user, 'establecimiento') and user.establecimiento:
        datos['establecimiento'] = user.establecimiento.nombre

    return datos
