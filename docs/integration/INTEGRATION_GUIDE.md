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

**IMPLEMENTADA Y PROBADA — INTEGRACIÓN TÉCNICA PRINCIPAL**

**Fecha de las verificaciones:** 14 de noviembre de 2026.
**Rama base:** `Build/Integration-US16-FrontendSprint3`.
**Commit de integración evaluado:** `e5699e0`.

Se comprobó la consulta de resultados persistidos mediante FastAPI, su presentación en Angular, la recuperación tras recargar y reiniciar los servidores, y los errores HTTP 404 y 409. La prioridad **MEDIA** se comprobó mediante ejecución directa de la función Python, **no** mediante una evaluación almacenada y visualizada de extremo a extremo. No se ha realizado validación clínica.

Las pruebas detalladas y las capturas recortadas se registran en el [Informe de pruebas US-16](../qa/INFORME_PRUEBAS_US16_2026-11-14.md).

## Alcance y componentes integrados

- **Frontend:** Angular, componentes `evaluation-results.ts` y `evaluation-results.html`.
- **Cliente HTTP:** `core/services/evaluation.ts`, método `getStoredEvaluationResults(evaluationId)`.
- **Backend:** FastAPI y servicios `ai_analysis_service.py`, `ai_results_service.py` y `clinical_priority_service.py`.
- **Persistencia:** PostgreSQL para análisis, resultados, indicadores de revisión y prioridad sugerida.
- **Servicio IA:** procesamiento de Retinopatía Diabética y Glaucoma mediante los modelos previamente configurados; su ejecución no es necesaria para realizar la consulta GET de resultados ya existentes.

La pantalla conserva también la visualización de la retinografía mediante la solicitud independiente de imagen del Backend. En las pruebas se comprobó que la imagen aparece en Angular; no se efectuó una auditoría de seguridad de S3 ni de las políticas de acceso al almacenamiento.

## Endpoints y comportamiento comprobado

### POST — Ejecución del análisis

`POST /api/v1/evaluations/{evaluation_id}/analysis`

El Backend ejecuta la verificación de calidad y, cuando corresponde, el análisis de RD y Glaucoma. Al completar correctamente ambos resultados:

- `ANALISIS_IA` queda en estado `COMPLETADO`;
- la retinografía queda `ANALIZADA`;
- se almacenan las clasificaciones y sus indicadores de confianza;
- se conservan los indicadores `requiere_revision` de ambos modelos;
- se calcula y persiste `prioridad_sugerida`.

La prueba previa del POST para la evaluación 2 obtuvo HTTP 200. Se comprobó también que volver a analizar una retinografía ya analizada es rechazado con HTTP 409. La consulta posterior de resultados no invoca nuevamente el POST.

### GET — Consulta de resultados persistidos

`GET /api/v1/evaluations/{evaluation_id}/results`

La ruta requiere autenticación institucional (`require_institutional_account`) y, por diseño, comprueba la pertenencia de la evaluación al establecimiento autenticado. **Las pruebas manuales aquí registradas no sustituyen pruebas de seguridad con cuentas de diferentes establecimientos.**

La respuesta incluye, entre otros:

- `id_evaluacion`, `id_analisis`, `estado` del análisis;
- metadatos de `retinografia`;
- `retinopatia_diabetica` y `glaucoma` (estado, resultado, confianza y `requiere_revision`);
- `requiere_revision` general;
- `prioridad_sugerida`;
- `resumen` (nullable);
- `aviso_soporte_clinico`.

**HTTP observados en las pruebas del 14/11/2026:**

| Escenario | Resultado observado | Comportamiento en Angular |
|---|---|---|
| Evaluación 2 con análisis completo | `200 OK` | Resultados RD y Glaucoma, advertencias y prioridad ALTA |
| Evaluación inexistente (`999999999`) | `404 Not Found` | «La evaluación retiniana no fue encontrada.» |
| Evaluación 3 existente, sin análisis | `409 Conflict` | «Los resultados todavía no están disponibles.» |

La evaluación 3 no tenía retinografía; una solicitud adicional a `/retinography/image` devolvió 404. Esto es independiente del 409 correspondiente a `/results`.

### GET — Imagen de retinografía

`GET /api/v1/evaluations/{evaluation_id}/retinography/image`

En las evaluaciones 1 y 2, Angular mostró la retinografía correspondiente junto a los resultados. Se verificó su persistencia visual después de F5, pero **no** se completaron pruebas de autorización, aislamiento entre establecimientos ni seguridad de almacenamiento.

## Reglas de prioridad sugerida

La función `calculate_suggested_priority()` utiliza la prioridad más alta entre RD y glaucoma, siempre que ambas categorías estén reconocidas. Si falta una clasificación o alguna categoría es desconocida, devuelve `None`.

| Clasificación RD | Prioridad RD |
|---|---|
| Sin indicios de Retinopatía Diabética | BAJA |
| Leve | BAJA |
| Moderada | MEDIA |
| Severa | ALTA |
| Proliferativa | ALTA |

| Clasificación glaucoma | Prioridad glaucoma |
|---|---|
| Bajo riesgo de Glaucoma | BAJA |
| Alto riesgo de Glaucoma | ALTA |

Orden: `BAJA < MEDIA < ALTA`.

**Prueba de cálculo:** se ejecutaron cinco aserciones Python y todas pasaron. Entre ellas, RD `Moderada` + glaucoma `Bajo riesgo de Glaucoma` devolvió **MEDIA**; RD `Moderada` + glaucoma `Alto riesgo de Glaucoma` devolvió **ALTA**. El caso con un resultado faltante devolvió `None`.

Las reglas son **experimentales y pendientes de validación por especialistas**. Las cifras de confianza de los modelos no deben presentarse como probabilidades clínicas sin justificar su interpretación y calibración.

## Persistencia de indicadores de revisión

La migración Alembic `c3cde9d8a14c` incorporó el campo nullable `RESULTADO_IA.requiere_revision`.

- Los análisis nuevos pueden almacenar los valores recibidos del Servicio IA.
- Los registros históricos pueden conservar `NULL`, que no debe equipararse automáticamente a `False`.
- En la evaluación 2, la respuesta del GET presentó `requiere_revision = true` para RD, glaucoma y el resultado general; Angular mostró ambas advertencias.

## Casos de prueba ejecutados

| Identificador | Caso | Evidencia | Veredicto |
|---|---|---|---|
| US16-T01 | Evaluación 2: RD Moderada, glaucoma Alto riesgo, prioridad ALTA | GET 200, JSON y pantalla | Aprobado |
| US16-T02 | Evaluación 1: RD Sin indicios, glaucoma Bajo riesgo, prioridad BAJA | Pantalla Angular | Aprobado (visual) |
| US16-T03 | Recargar evaluación 2 con F5 | GET 200 y resultados reaparecen | Aprobado |
| US16-T04 | Consultar evaluación inexistente `999999999` | GET 404 y mensaje Angular | Aprobado |
| US16-T05 | Consultar evaluación 3 sin análisis | GET 409 y mensaje Angular | Aprobado |
| US16-T06 | Cálculo Python de prioridades y resultado faltante | 5 aserciones correctas, incluida MEDIA | Aprobado (función) |
| US16-T07 | «Finalizar evaluación» de evaluación 2 | Navegación a `/patients/1` | Aprobado (solo navegación) |
| US16-T08 | Detener/reiniciar FastAPI y Angular | Servicios y resultados de evaluación 2 disponibles | Aprobado (operación local) |
| US16-T09 | Commit de integración y publicación de rama | `e5699e0`, push de rama de integración | Aprobado |
| US16-T10 | Prioridad MEDIA persistida y visualizada en Angular | No se creó caso E2E | Pendiente |

Los valores observados en la evaluación 2 incluyen `id_analisis = 14`, confianza RD ~39,37 % y confianza glaucoma ~3,67 %. En la evaluación 1, la pantalla mostró RD ~99,23 % y glaucoma ~58,12 %. Son **indicadores del modelo**, no probabilidades clínicas validadas.

## Integración Angular y comportamiento de navegación

El componente de resultados solicita al Backend los datos persistidos al acceder a `/evaluations/{evaluationId}/results`; por ello, una recarga F5 permite recuperar los resultados sin depender únicamente del estado temporal del frontend.

El botón **«Finalizar evaluación»** está conectado a `goToPatient()` y **solo navega** a `/patients/{id}`. En las pruebas, desde la evaluación 2 redirigió a `/patients/1`. **No cambia el estado a `FINALIZADA` ni realiza cierre formal en PostgreSQL.**

El botón **«Ver»** de la pestaña de historial del paciente continúa sin acción implementada; el enlace provisional añadido durante las pruebas fue revertido deliberadamente para no invadir la funcionalidad pendiente del frontend.

## Observaciones y pendientes identificados

1. **Consistencia de estados:** las evaluaciones 1 y 2 figuraban `PENDIENTE` en `evaluacion_retiniana` pese a disponer de análisis IA `COMPLETADO`. Definir claramente la diferencia entre estado de evaluación, análisis y retinografía antes de corregirlos; no modificarlos manualmente.
2. **Cierre formal:** establecer el significado clínico y transaccional de «Finalizar evaluación» y sus criterios de aceptación.
3. **Historial:** implementar y validar la acción «Ver» y la navegación correspondiente, coordinando el trabajo de frontend.
4. **Prueba MEDIA extremo a extremo:** observar un caso legítimo/controlado con resultado persistido y visualización en Angular; no alterar los resultados existentes para forzar un caso.
5. **Seguridad/autorización:** probar acceso sin sesión, acceso denegado y aislamiento por establecimiento para resultados e imagen. La existencia de validaciones en código no equivale a prueba de seguridad concluida.
6. **Resumen «Sin indicios»:** falta una verificación específica del campo `resumen` en la respuesta y su presentación, cuando aplique.
7. **Mensajes y estilos:** en los escenarios 404/409, la pantalla sigue intentando obtener la imagen; revisar manejo de estado vacío y apariencia del botón «Volver a la retinografía».
8. **Interpretación clínica:** validar con oftalmólogos la matriz ALTA/MEDIA/BAJA, las advertencias y los indicadores de confianza, especialmente los valores bajos asociados a categorías de alto riesgo.
9. **Reproducibilidad:** en una terminal WSL se observó `conda: command not found` aun cuando Python pudo iniciar Uvicorn; revisar la inicialización de Conda sin confundirlo con un fallo del backend.
10. **Configuración de modelos en otro equipo:** la tabla `modelo_ia` estaba vacía y el análisis mostraba un error de configuración; se confirmó su resolución mediante `app/scripts/seed_ai_models.py`. Esto no representa un error de inferencia del modelo.

## Referencias internas

- [Informe detallado de pruebas y evidencias](../qa/INFORME_PRUEBAS_US16_2026-11-14.md).
- `retina-support-backend/app/services/clinical_priority_service.py`.
- `retina-support-backend/app/services/ai_results_service.py`.
- `retina-support-frontend/src/app/pages/evaluations/evaluation-results/`.

**Nota de alcance:** las pruebas corresponden al prototipo en un entorno local de desarrollo, no a un despliegue clínico, certificación regulatoria ni validación diagnóstica.