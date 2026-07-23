# Planificación Técnica: Módulo de Bodega e Inventario

## 1. Introducción

El módulo de Bodega e Inventario para el ERP SAG está diseñado para gestionar de forma eficiente, segura y auditable el
flujo de recursos dentro de la institución. Su arquitectura multi-establecimiento permite la coexistencia de múltiples
inventarios independientes, asegurando que las operaciones de una bodega no afecten a las demás.

## 2. Arquitectura del Módulo

### 2.1 Multi-establecimiento y Multi-bodega

El sistema se estructura en una jerarquía de tres niveles:

1. **Establecimiento**: Entidad superior (ej. Hospital, Centro de Salud).
2. **Bodega**: Unidad administrativa dentro del establecimiento (ej. Farmacia, Economato, TI).
3. **Existencia**: El stock real de un producto específico dentro de una bodega particular.

### 2.2 Diseño Genérico de Productos

Para soportar áreas tan diversas como fármacos, insumos médicos y equipos computacionales, se propone un modelo de *
*Producto** base altamente extensible, complementado con categorías y atributos dinámicos.

---

## 3. Propuesta de Modelos de Datos

### 3.1 Modelos Base

* **Bodega**:
    * `nombre` (CharField)
    * `establecimiento` (ForeignKey -> Establecimiento)
    * `tipo_bodega` (Choices: Farmacia, Insumos, Activos Fijos, etc.)
    * `encargado` (ForeignKey -> User)
    * `activo` (Boolean)

* **Categoria**:
    * `nombre` (CharField)
    * `descripcion` (TextField)
    * `parent` (ForeignKey -> 'self' para jerarquías)

* **Producto**:
    * `codigo_interno` (CharField, unico)
    * `codigo_barra` (CharField, opcional)
    * `nombre` (CharField)
    * `descripcion` (TextField)
    * `categoria` (ForeignKey -> Categoria)
    * `unidad_medida` (Choices: Unidad, Caja, Frasco, etc.)
    * `stock_minimo` (DecimalField) - Para alertas de reposición.

### 3.2 Gestión de Stock y Movimientos

* **Existencia (Stock Actual)**:
    * `bodega` (ForeignKey -> Bodega)
    * `producto` (ForeignKey -> Producto)
    * `cantidad` (DecimalField)
    * `precio_promedio_ponderado` (DecimalField) - Para valorización de inventario.
    * *Índice único (bodega, producto).*

* **Movimiento (Cabecera)**:
    * `tipo_movimiento` (Choices: INGRESO, SALIDA, TRANSFERENCIA, AJUSTE)
    * `bodega_origen` (ForeignKey -> Bodega, null=True)
    * `bodega_destino` (ForeignKey -> Bodega, null=True)
    * `fecha` (DateTimeField)
    * `usuario` (ForeignKey -> User)
    * `referencia_documento` (CharField) - Ej: N° de Factura o Guía.
    * `archivo_pdf` (FileField) - Para almacenar la factura o guía escaneada.
    * `observacion` (TextField)
    * `estado` (Choices: BORRADOR, PROCESADO, ANULADO)

* **MovimientoDetalle**:
    * `movimiento` (ForeignKey -> Movimiento)
    * `producto` (ForeignKey -> Producto)
    * `cantidad` (DecimalField)
    * `precio_unitario` (DecimalField)
    * `lote` (CharField, opcional) - Crítico para fármacos.
    * `fecha_vencimiento` (DateField, opcional)

### 3.3 Auditoría e Inventario Físico

* **InventarioFisico**:
    * `bodega` (ForeignKey -> Bodega)
    * `fecha_corte` (DateTimeField)
    * `estado` (ABIERTO, CERRADO)
* **InventarioDetalle**:
    * `inventario_fisico` (ForeignKey -> InventarioFisico)
    * `producto` (ForeignKey -> Producto)
    * `stock_sistema` (DecimalField)
    * `stock_fisico` (DecimalField)
    * `diferencia` (DecimalField)

---

## 4. Flujos de Trabajo

### 4.1 Flujo de Ingreso (Compras/Donaciones)

1. El usuario selecciona la **Bodega Destino**.
2. Completa datos del proveedor y referencia (N° Factura).
3. **Adjunta el PDF de la factura**.
4. Agrega los productos, cantidades y precios.
5. Al "Procesar":
    * Se crea/actualiza la `Existencia` en la bodega destino.
    * Se recalcula el Precio Promedio Ponderado (PPP).
    * El movimiento queda bloqueado (inmutable).

### 4.2 Flujo de Salida (Consumo/Entrega)

1. El usuario selecciona la **Bodega Origen**.
2. El sistema valida en tiempo real que haya stock suficiente en `Existencia`.
3. Se registran los productos a retirar.
4. Al "Procesar":
    * Se descuenta la cantidad de `Existencia`.
    * Si el stock cae bajo el `stock_minimo`, se genera una alerta.

### 4.3 Flujo de Transferencia (Entre Bodegas)

1. Se define **Bodega Origen** y **Bodega Destino**.
2. El sistema valida stock en el origen.
3. Al "Procesar":
    * Se realiza una salida de la bodega origen.
    * Se realiza un ingreso en la bodega destino.
    * Ambas operaciones quedan vinculadas por el mismo `MovimientoID`.

---

## 5. Reglas de Negocio Críticas

1. **Integridad de Stock**: El stock real (`Existencia`) NUNCA debe editarse manualmente. Solo los procesos de
   `Movimiento` pueden alterar la cantidad.
2. **No Stock Negativo**: El sistema no permitirá procesar salidas o transferencias si la bodega origen no cuenta con la
   cantidad suficiente del producto.
3. **Inmutabilidad**: Una vez que un movimiento pasa a estado "PROCESADO", no puede ser editado ni eliminado. Si hubo un
   error, se debe realizar un "Movimiento de Anulación" o un "Ajuste de Inventario" que deje rastro de auditoría.
4. **Trazabilidad**: Cada movimiento debe registrar IP, User Agent y Usuario (utilizando los servicios ya implementados
   en el `core`).
5. **Multitenancy Lógico**: Los usuarios solo pueden ver y operar en las bodegas de los establecimientos a los que
   tienen permiso de acceso.

---

## 6. Recomendaciones de Implementación y Escalabilidad

* **Capa de Servicios**: Toda la lógica de cálculo de stock y validaciones debe vivir en `InventoryService`. Las vistas
  solo deben orquestar la petición HTTP.
* **Transacciones**: El procesamiento de un movimiento debe estar envuelto en `transaction.atomic()` para asegurar que,
  si falla el ingreso de un ítem, no se descuente el stock del encabezado.
* **Lotes y Vencimientos**: Aunque el modelo es genérico, se deben incluir los campos `lote` y `fecha_vencimiento` como
  opcionales. Para la bodega de fármacos serán obligatorios, mientras que para la de computación podrán quedar vacíos.
* **Documentos Dinámicos**: Usar una estructura de almacenamiento organizada para los PDFs (ej.
  `media/inventario/facturas/YYYY/MM/`).
* **API Ready**: Diseñar los servicios pensando en que en el futuro los movimientos podrían ser gatillados por
  integraciones externas (ej. Central de Abastecimiento).
* **Campos Personalizados**: Si un área requiere campos muy específicos (ej. RAM/Procesador para computación), se
  recomienda usar un campo `data` (JSONField) en el modelo `Producto` para no ensuciar la tabla principal.

---

## 7. Casos de Uso Complementarios (Identificados)

* **Alertas de Vencimiento**: Reporte de fármacos próximos a vencer en los próximos 3 meses.
* **Kardex de Producto**: Reporte cronológico de todos los movimientos de un producto específico en una bodega
  determinada.
* **Valorización de Inventario**: Cálculo del valor total de la bodega basado en el PPP.
* **Kit de Productos**: Capacidad de definir "Combos" o "Sets" (ej. Kit de Curación) que descuenten múltiples insumos a
  la vez.
