# Planificación Técnica: Módulo de Gestión de Activos TIC

Este documento detalla la arquitectura y el diseño funcional para el nuevo módulo de Gestión de Activos TIC del ERP SAG,
diseñado para ser flexible, escalable y basado en eventos.

## 1. Arquitectura de Modelos

La arquitectura propuesta utiliza un enfoque híbrido: una identidad estática para el activo y un sistema de
características dinámicas (EAV) para la flexibilidad de tipos, junto con un historial de movimientos como fuente de
verdad del estado actual.

### Modelos y Responsabilidades

| Modelo                    | Responsabilidad                                                                      |
|:--------------------------|:-------------------------------------------------------------------------------------|
| **TipoActivo**            | Clasifica los activos (Computador, UPS, Router, etc.).                               |
| **CampoTipoActivo**       | Define qué atributos dinámicos tiene cada tipo (RAM, Voltaje, etc.).                 |
| **OpcionCampoTipoActivo** | Provee las opciones para campos de tipo "Select" manuales.                           |
| **Activo**                | Almacena la identidad inmutable del dispositivo (Serie, Inventario, Marca, Modelo).  |
| **ActivoCaracteristica**  | Almacena el valor de cada atributo dinámico para un activo específico.               |
| **Ip**                    | Catálogo centralizado de direccionamiento IP (Dirección, Máscara, Gateway, VLAN).    |
| **TipoMovimiento**        | Catálogo de tipos de eventos (Ingreso, Asignación, Baja, etc.).                      |
| **MovimientoActivo**      | Historial transaccional. Es la fuente de verdad para la ubicación, responsable e IP. |

---

## 2. Relaciones entre Modelos

1. **TipoActivo 1:N CampoTipoActivo**: Un tipo define múltiples campos.
2. **CampoTipoActivo 1:N OpcionCampoTipoActivo**: Un campo tipo Select puede tener múltiples opciones manuales.
3. **TipoActivo 1:N Activo**: Cada activo pertenece a un tipo.
4. **Activo 1:N ActivoCaracteristica**: Un activo tiene múltiples valores para sus campos definidos.
5. **CampoTipoActivo 1:N ActivoCaracteristica**: Relaciona el valor con su definición.
6. **Activo 1:N MovimientoActivo**: Un activo acumula historial de movimientos.
7. **TipoMovimiento 1:N MovimientoActivo**: Clasifica el movimiento.
8. **MovimientoActivo N:1 Funcionario/UnidadOrganizacional**: Registra a quién y dónde está el activo.
9. **MovimientoActivo N:1 Ip**: Registra qué IP tiene asignada el activo en ese momento.

---

## 3. Estrategia de Campos Tipo "Select"

Para soportar tanto opciones manuales como mantenedores existentes (Marca, Modelo, Toner, etc.), se propone la siguiente
lógica en `CampoTipoActivo`:

- **Atributos Adicionales en CampoTipoActivo**:
    - `source_type`: ChoiceField (Manual, Mantenedor Externo).
    - `source_model`: CharField (Almacena el `app_label.ModelName`, ej: `gestion_tic.Toner`).
- **Lógica de Renderizado**:
    - Si `source_type` es "Manual", el formulario carga las opciones desde `OpcionCampoTipoActivo`.
    - Si `source_type` es "Mantenedor Externo", el sistema utiliza `ContentType` o una búsqueda dinámica de modelo para
      listar los objetos activos del modelo especificado en `source_model`.
    - Esto evita la duplicidad de datos y permite reutilizar catálogos existentes.

---

## 4. Ciclo de Vida del Activo

El estado actual no se guarda en un campo `estado` del `Activo`, sino que se deduce del `tipo_movimiento` del último
registro en `MovimientoActivo`.

1. **Ingreso**: El activo se crea y se registra su primer movimiento de tipo "Ingreso" (Estado: Bodega).
2. **Operación**:
    - **Asignación**: Se vincula a un funcionario y unidad.
    - **Traslado**: Cambio de ubicación/unidad.
    - **Reparación**: El activo sale temporalmente a servicio técnico.
3. **Baja**: Movimiento final que marca el fin de la vida útil del activo en la organización.

---

## 5. Flujo del Sistema

1. **Configuración**: El administrador crea un `TipoActivo` (ej: Impresora) y le asigna `CampoTipoActivo` (ej: "Tipo de
   Toner" de tipo Select apuntando al mantenedor `Toner`).
2. **Registro**: Se crea el `Activo` con sus datos básicos. Automáticamente, el formulario despliega los campos
   dinámicos definidos para su tipo.
3. **Activación**: Se genera el primer `MovimientoActivo` (Ingreso).
4. **Consulta**: Al ver la ficha del activo, el sistema busca el último movimiento para mostrar quién lo tiene, dónde
   está y qué IP usa.

---

## 6. Reglas de Negocio y Validaciones

- **Unicidad**: Serie y Número de Inventario deben ser únicos en `Activo`.
- **IPs**: Una IP con estado "Activa" en el catálogo no puede ser asignada a otro movimiento hasta que el activo
  anterior la libere (mediante un nuevo movimiento que no la incluya o que sea de Devolución/Baja).
- **Obligatoriedad**: Las características marcadas como obligatorias en `CampoTipoActivo` deben validarse en el
  formulario dinámico.
- **Integridad de Movimientos**: No se puede registrar un movimiento de "Asignación" si el activo está en estado "Baja".
- **Consistencia de IP**: Si un activo cambia de IP, el catálogo de `Ip` debe actualizar los estados de la IP anterior (
  Disponible) y la nueva (Activa).

---

## 7. Casos de Uso

- **Inventariado Rápido**: Registro masivo de activos con specs base.
- **Trazabilidad de Responsables**: Consultar quién tuvo un notebook específico hace 6 meses (revisando el historial de
  movimientos).
- **Auditoría de Red**: Listar todos los activos asociados a una VLAN específica a través de sus IPs actuales.
- **Control de Préstamos**: Registrar la salida temporal de un proyector a un funcionario y su posterior devolución a
  bodega.

---

## 8. Recomendaciones de Implementación

- **Django Forms**: Utilizar un `BaseModelForm` personalizado que genere dinámicamente los campos extra basados en el
  `tipo_activo` seleccionado (usando AJAX para cargar los campos al cambiar el tipo).
- **Desempeño**: Para evitar el problema de N+1 consultas al listar activos con su "estado actual", utilizar
  `Window functions` o `Subqueries` en el ORM de Django para traer el último movimiento de cada activo en una sola
  consulta.
- **Señales (Signals)**: Utilizar `post_save` en `MovimientoActivo` para actualizar el estado de las IPs en el modelo
  `Ip`.

---

## 9. Análisis de Inconsistencias y Mejoras Detectadas

- **Marca y Modelo**: El usuario solicitó Marca y Modelo en `Activo`, pero en el sistema actual existen como modelos
  independientes. Se recomienda mantener la relación `ForeignKey` a esos modelos en `Activo` en lugar de campos de
  texto, para mantener la integridad.
- **Historial de IPs**: El sistema propuesto elimina la tabla de historial de IP. Esto es correcto siempre que el
  `MovimientoActivo` capture siempre la IP actual. Si un activo cambia de IP sin cambiar de responsable o ubicación, se
  debe registrar un movimiento de tipo "Cambio de IP".
- **Campos Dinámicos en Listados**: Mostrar campos dinámicos (ej: RAM) en el listado general de activos puede ser
  complejo para filtrar. Se recomienda definir en `CampoTipoActivo` un flag `mostrar_en_listado`.
- **Eliminación de Modelos**: Una vez implementado este sistema, los modelos `Equipo` y `Celular` pueden ser migrados a
  la nueva estructura de `Activo` y luego eliminados.
