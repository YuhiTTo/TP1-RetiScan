# Guía de Integración — RetiScan

Este documento registra cambios implementados y comprobados que afectan la integración entre Frontend, Backend y Servicio IA.

La información se actualiza únicamente después de verificar el comportamiento mediante código y/o pruebas funcionales. Las funcionalidades futuras no deben documentarse como implementadas.

---

# US-11 — Validación de la retinografía seleccionada

## Estado

**IMPLEMENTADA Y PROBADA**

## Objetivo funcional

US-11 valida la retinografía seleccionada antes de permitir que continúe hacia las siguientes etapas del flujo.

La implementación contempla:

- aceptar imágenes en formatos permitidos que puedan ser leídas correctamente;
- rechazar archivos vacíos;
- rechazar extensiones no permitidas;
- rechazar imágenes dañadas o ilegibles;
- comprobar que el formato real detectado en el contenido corresponda a un formato admitido.

## Endpoint

`PUT /api/v1/evaluations/{evaluation_id}/retinography`

Respuesta exitosa:

`HTTP 200 OK`

El endpoint utiliza como modelo de respuesta:

`RetinographyResponse`

## Autenticación

El endpoint está protegido mediante:

`require_institutional_account`

La cuenta institucional autenticada determina el establecimiento utilizado para consultar la evaluación.

## Formato de envío

La imagen se recibe mediante:

`UploadFile`

en un campo denominado:

`file`

Por utilizar `File(...)` de FastAPI, la carga se realiza como formulario multipart.

Campo esperado:

`file`

## Formatos admitidos

Las extensiones permitidas son:

- `.jpg`
- `.jpeg`
- `.png`

La extensión del archivo no es la única validación realizada.

Después de leer el contenido, Pillow verifica que la imagen pueda abrirse correctamente mediante:

`Image.open(...).verify()`

Posteriormente se vuelve a abrir la imagen para obtener:

- ancho;
- alto;
- formato detectado.

Los formatos internos admitidos son:

- `jpeg`
- `png`

Por lo tanto, un archivo no es aceptado únicamente por tener una extensión válida; su contenido también debe poder ser interpretado como una imagen JPEG o PNG.

## Validaciones y respuestas HTTP

### Evaluación inexistente

Respuesta:

`HTTP 404 Not Found`

```json
{
  "detail": "La evaluación retiniana no fue encontrada."
}
```

### Archivo vacío

Respuesta:

`HTTP 422 Unprocessable Entity`

```json
{
  "detail": "La retinografía seleccionada está vacía."
}
```

### Formato no admitido

Respuesta:

`HTTP 415 Unsupported Media Type`

```json
{
  "detail": "Formato de retinografía no admitido. Utilice JPG, JPEG o PNG."
}
```

Este caso puede producirse si la extensión no está permitida o si el formato real detectado en el contenido no corresponde a JPEG o PNG.

### Imagen dañada o ilegible

Respuesta:

`HTTP 422 Unprocessable Entity`

```json
{
  "detail": "La retinografía no pudo ser leída correctamente."
}
```

### Almacenamiento no configurado

Respuesta:

`HTTP 503 Service Unavailable`

```json
{
  "detail": "El almacenamiento de retinografías no está configurado."
}
```

### Error durante el almacenamiento

Respuesta:

`HTTP 502 Bad Gateway`

```json
{
  "detail": "No se pudo almacenar la retinografía."
}
```

### Conflicto durante el registro

Respuesta:

`HTTP 409 Conflict`

```json
{
  "detail": "No se pudo registrar la retinografía."
}
```

## Datos registrados

Cuando la imagen supera las validaciones, la entidad `RETINOGRAFIA` mantiene información como:

- `id_retinografia`
- `id_evaluacion`
- `nombre_archivo`
- `formato`
- `tamano_bytes`
- `ancho_px`
- `alto_px`
- `ruta_original_s3`
- `estado_validacion`
- `calidad_imagen`
- `estado`
- `fecha_carga`

## Estado después de una carga válida

Tanto al registrar una nueva retinografía como al reemplazar una existente, la implementación establece:

`estado_validacion = VALIDADA`

`calidad_imagen = null`

`estado = CARGADA`

El valor `calidad_imagen = null` indica que la nueva imagen todavía debe pasar por la verificación de calidad correspondiente a US-12.

## Reemplazo de retinografía

Antes de crear un nuevo registro, el servicio consulta si la evaluación ya posee una retinografía asociada.

Si no existe, crea una nueva entidad `RETINOGRAFIA`.

Si ya existe, actualiza el mismo registro con:

- nuevo nombre de archivo;
- nuevo formato;
- nuevo tamaño;
- nuevas dimensiones;
- nueva ruta de almacenamiento.

También reinicia:

`estado_validacion = VALIDADA`

`calidad_imagen = null`

`estado = CARGADA`

El reemplazo de una retinografía se permite únicamente cuando la evaluación no se encuentra finalizada y la retinografía no tiene el estado `ANALIZADA`.

Cuando la retinografía ya fue analizada correctamente o la evaluación se encuentra `FINALIZADA`, el Backend rechaza la operación mediante HTTP 409 Conflict.

Cuando se permite un reemplazo, se actualizan los metadatos de la imagen, se establece `estado = CARGADA`, se reinicia `calidad_imagen = null` y se elimina la prioridad sugerida anterior. La nueva imagen debe superar nuevamente la verificación de calidad de US-12 antes de continuar con el análisis automatizado.

## Persistencia

Después de crear o actualizar la retinografía se ejecuta:

`db.commit()`

y posteriormente:

`db.refresh(retinography)`

Si ocurre un `IntegrityError`, se ejecuta:

`db.rollback()`

antes de propagar el error.

## Consideraciones para integración con Frontend

Para integrarse con este endpoint, el Frontend debe:

- enviar una única imagen mediante el campo `file`;
- utilizar el endpoint asociado a la evaluación correspondiente;
- contemplar los códigos `404`, `415`, `422`, `409`, `502` y `503`;
- permitir que el usuario sustituya una retinografía cuando corresponda;
- no asumir que `VALIDADA` significa que la calidad visual ya fue aprobada.

La validación de US-11 confirma que el archivo puede ser utilizado por el sistema.

La evaluación de calidad visual pertenece a US-12 y se ejecuta posteriormente.

---

# US-12 — Verificación de calidad mínima de la retinografía

## Estado

**IMPLEMENTADA Y PROBADA**

## Objetivo funcional

US-12 determina si una retinografía válida posee condiciones mínimas para continuar hacia el procesamiento y análisis automatizado.

El resultado de calidad puede ser:

- `SUFICIENTE`
- `INSUFICIENTE`

## Posición dentro del flujo

La verificación de calidad se ejecuta antes de crear un nuevo registro de análisis IA y antes de crear las ejecuciones correspondientes a los modelos.

Flujo implementado:

`Retinografía cargada`

→ `Verificación de calidad`

→ `SUFICIENTE / INSUFICIENTE`

Si la calidad es suficiente, el flujo puede continuar hacia el análisis automatizado.

Si la calidad es insuficiente, no se crean los registros de análisis correspondientes a ese intento.

## Endpoint utilizado por el Frontend/Backend principal

`POST /api/v1/evaluations/{evaluation_id}/analysis`

Antes de ejecutar los modelos, el Backend principal solicita internamente al Servicio IA la evaluación de calidad de la retinografía almacenada.

## Autenticación — US-12

El endpoint:

`POST /api/v1/evaluations/{evaluation_id}/analysis`

requiere autenticación mediante:

`require_institutional_account`

La cuenta institucional autenticada determina el establecimiento desde el cual se consulta la evaluación.

## Request — US-12

La solicitud no requiere un cuerpo JSON.

El identificador de la evaluación se envía directamente en la URL mediante:

`evaluation_id`

Ejemplo:

`POST /api/v1/evaluations/2/analysis`

## Respuesta exitosa

Cuando el flujo puede ejecutarse correctamente, el endpoint responde:

`HTTP 200 OK`

utilizando el modelo de respuesta:

`AIAnalysisResponse`

## Servicio IA

El Servicio IA dispone de la operación interna:

`POST /api/v1/quality`

El Backend principal la consume utilizando la identificación de la evaluación y la ruta de la retinografía almacenada.

## Criterios de calidad implementados

La evaluación considera:

- claridad;
- iluminación;
- contraste;
- disponibilidad técnica de una región retinal utilizable.

Las métricas calculadas incluyen:

- `clarity_gradient_p90`
- `dark_ratio_30`
- `contrast_cv`
- `fov_area_ratio`
- `fov_width_ratio`
- `fov_height_ratio`
- `fov_center_offset`

Los umbrales utilizados para los tres controles principales de producción son:

`clarity_gradient_p90 >= 16.06225775`

`dark_ratio_30 <= 0.33113740`

`contrast_cv <= 0.63830344`

Las métricas geométricas de FOV se conservan para trazabilidad y reproducibilidad experimental. La decisión final de producción utiliza el FOV como verificación de que exista una región retinal técnicamente utilizable.

## Persistencia

Después de recibir el resultado del Servicio IA, el Backend actualiza:

`retinografia.calidad_imagen`

con uno de los siguientes valores:

`SUFICIENTE`

o:

`INSUFICIENTE`

y persiste el resultado antes de continuar con el flujo.

## Calidad insuficiente

Cuando:

`calidad_imagen = INSUFICIENTE`

el Backend detiene el flujo antes de crear un nuevo `ANALISIS_IA` y sus correspondientes `EJECUCION_MODELO`.

La respuesta comprobada del endpoint de análisis es:

`HTTP 422 Unprocessable Entity`

con:

```json
{
  "detail": "La retinografía no cumple con la calidad mínima requerida para realizar el análisis."
}
```

En la prueba funcional realizada con una retinografía clasificada como insuficiente se comprobó en PostgreSQL que no se crearon nuevos registros de análisis ni ejecuciones de modelos para ese intento.

## Calidad suficiente

Cuando:

`calidad_imagen = SUFICIENTE`

el Backend continúa con el flujo de análisis.

Después de superar US-12 se crean:

- un registro `ANALISIS_IA`;
- una ejecución para el modelo de Retinopatía Diabética;
- una ejecución para el modelo de Glaucoma.

Posteriormente se solicita el análisis al Servicio IA.

## Reemplazo después de calidad insuficiente

Se comprobó el siguiente flujo:

`INSUFICIENTE`

→ reemplazo de retinografía

→ `calidad_imagen = null`

→ nueva solicitud de análisis

→ nueva ejecución de US-12

En la prueba realizada, después de sustituir la imagen insuficiente por una imagen que superó la evaluación de calidad, el análisis pudo continuar normalmente.

## FOV no utilizable

También se probó el comportamiento con una imagen decodificable en la que no era posible preparar una región retinal técnicamente utilizable.

Ese caso se clasifica como:

`INSUFICIENTE`

por el criterio:

`fov`

y no se continúa hacia los modelos.

## Otros códigos HTTP contemplados

### Evaluación inexistente

`HTTP 404 Not Found`

```json
{
  "detail": "La evaluación retiniana no fue encontrada."
}
```

### Evaluación sin retinografía

`HTTP 409 Conflict`

```json
{
  "detail": "La evaluación no tiene una retinografía registrada."
}
```

### Configuración inválida de modelos IA

`HTTP 503 Service Unavailable`

Este caso puede producirse cuando no se encuentran configurados todos los modelos activos requeridos o existe una configuración incompatible de modelos activos.

### Calidad insuficiente

`HTTP 422 Unprocessable Entity`

```json
{
  "detail": "La retinografía no cumple con la calidad mínima requerida para realizar el análisis."
}
```

### Error de preprocesamiento

`HTTP 422 Unprocessable Entity`

El mensaje depende del detalle devuelto durante el preprocesamiento.

### Error de ejecución o comunicación con el Servicio IA

`HTTP 502 Bad Gateway`

El mensaje depende del error técnico producido durante la ejecución.

## Consideraciones de integración con Frontend

Para integrarse con el Backend actual, el Frontend debe contemplar al menos los siguientes comportamientos.

### Análisis permitido

Si la retinografía supera US-12, la solicitud puede continuar hacia el análisis automatizado.

### HTTP 422 por calidad insuficiente

El Frontend debe poder presentar al usuario el mensaje devuelto por el Backend y ofrecer el flujo existente de reemplazo de retinografía.

En este caso no se generan nuevos resultados de Retinopatía Diabética ni Glaucoma correspondientes a ese intento.

---

# Regla de actualización de esta guía

Las siguientes historias no deben añadirse como implementadas hasta después de haber sido desarrolladas y probadas.

Para cada historia nueva se registrará únicamente información comprobada sobre:

- endpoint implementado;
- método HTTP;
- request real;
- response real;
- códigos HTTP observados;
- cambios de persistencia;
- nuevas reglas de negocio;
- impacto sobre la integración del Frontend;
- pruebas realizadas;
- archivos principales modificados cuando resulte útil para la integración.

Estados utilizados:

- `IMPLEMENTADA Y PROBADA`
- `IMPLEMENTADA - PENDIENTE DE PRUEBA`
- `PENDIENTE`


---

# US-16 — Consulta y presentación de resultados de IA

## Estado

**BACKEND IMPLEMENTADO Y PROBADO PARCIALMENTE**

La recuperación de resultados está implementada y probada.
La integración final con Angular y la visualización de la
retinografía deben verificarse antes de cerrar US-16.

## Ejecución del análisis

Endpoint:

`POST /api/v1/evaluations/{evaluation_id}/analysis`

El Backend ejecuta los modelos de Retinopatía Diabética
y Glaucoma mediante el Servicio IA.

Cuando ambos modelos terminan correctamente:

- El análisis queda en estado `COMPLETADO`.
- La retinografía pasa a estado `ANALIZADA`.
- Se almacenan los resultados y niveles de confianza.
- Se registra `requiere_revision` para cada modelo.
- Se calcula y almacena `prioridad_sugerida`.

## Prioridad sugerida

La prioridad se calcula a partir de las dos clasificaciones:

- `ALTA`
- `MEDIA`
- `BAJA`

Se utiliza la mayor prioridad correspondiente a los
resultados de ambas patologías.

La prioridad constituye información de soporte clínico,
no una decisión médica definitiva.

## Persistencia de advertencias

Se incorporó el campo nullable:

`RESULTADO_IA.requiere_revision`

Mediante la migración Alembic:

`c3cde9d8a14c`

Los nuevos análisis almacenan los indicadores devueltos
por el Servicio IA.

Los registros históricos pueden conservar `NULL`, que no
debe interpretarse automáticamente como `False`.

## Consulta de resultados

Endpoint:

`GET /api/v1/evaluations/{evaluation_id}/results`

Autenticación:

`require_institutional_account`

La consulta verifica que la evaluación pertenezca al
establecimiento autenticado.

Recupera desde PostgreSQL:

- Identificador y estado del análisis.
- Metadatos de la retinografía.
- Clasificación de Retinopatía Diabética.
- Clasificación de riesgo de Glaucoma.
- Confianza independiente por modelo.
- Indicador de revisión independiente por modelo.
- Prioridad sugerida.
- Resumen `Sin indicios de las patologías evaluadas`
  cuando corresponde.
- Aviso de que los resultados y la prioridad no
  sustituyen el criterio del oftalmólogo.

El GET no vuelve a ejecutar los modelos CNN.

## Reglas de protección

No se permite reemplazar la retinografía si está
`ANALIZADA` o la evaluación está `FINALIZADA`.

Tampoco se permite repetir el análisis sobre una
retinografía `ANALIZADA` o evaluación `FINALIZADA`.

Estos intentos son rechazados mediante HTTP 409.

Las evaluaciones nuevas pueden utilizar imágenes
idénticas a las de otras evaluaciones.

## Pruebas funcionales realizadas

Evaluación 2, análisis 14:

- POST de análisis: HTTP 200.
- Retinopatía Diabética: Moderada.
- Glaucoma: Alto riesgo de Glaucoma.
- Ambos indicadores `requiere_revision`: `true`.
- Prioridad sugerida: `ALTA`.
- Persistencia verificada en PostgreSQL.
- GET de resultados: HTTP 200.
- Reanálisis de la evaluación 2: HTTP 409.

## Funcionalidades pendientes de verificar

- Presentación completa de resultados en Angular.
- Visualización segura de la retinografía almacenada en S3.
- Prueba específica del resumen `Sin indicios`.
- Pruebas adicionales de acceso y errores del GET.

Estas funcionalidades no se consideran todavía
completamente validadas.