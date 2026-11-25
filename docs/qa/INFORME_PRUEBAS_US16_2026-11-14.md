# RetiScan — Informe de pruebas funcionales e integración US-16

**Fecha de ejecución:** 14 de noviembre de 2026
**Tipo de documento:** Registro de pruebas / evidencia de integración técnica
**Estado:** Integración principal validada; pendientes funcionales y clínicos identificados
**Rama publicada:** `Build/Integration-US16-FrontendSprint3`
**Commit:** `e5699e0` — `Integra backend US-16 con frontend Sprint 3`
**Repositorio:** https://github.com/YuhiTTo/TP1-RetiScan
**Entorno:** ejecución local de desarrollo; no equivale a certificación ni validación clínica.

> **Nota de confidencialidad:** los identificadores de evaluación pertenecen al entorno local de pruebas. Las capturas adjuntas están recortadas para evitar nombres de pacientes, documentos de identidad y credenciales.

## 1. Propósito y alcance

Verificar la integración del backend FastAPI con el frontend Angular para consultar los resultados de un análisis retiniano previamente registrado, presentar los resultados independientes de retinopatía diabética (RD) y glaucoma, mostrar advertencias de revisión y una **prioridad sugerida** (ALTA, MEDIA o BAJA). Evaluar respuestas para evaluaciones inexistentes y evaluaciones sin análisis. Comprobar la navegación actual del botón «Finalizar evaluación» y la capacidad de reiniciar los servicios.

**Fuera de alcance de esta verificación:** validación clínica, exactitud diagnóstica, calibración probabilística de los modelos, clasificación MEDIA persistida extremo a extremo, seguridad/autorización exhaustiva, registro de observaciones médicas y cierre formal de evaluaciones.

## 2. Entorno, precondiciones y trazabilidad

| Elemento | Configuración o evidencia |
|---|---|
| Frontend | Angular, `http://localhost:4200` (sesión institucional de prueba) |
| Backend | FastAPI/Uvicorn, `http://127.0.0.1:8000` |
| Base de datos | PostgreSQL local (`retina_support_db`) |
| Consulta principal | `GET /api/v1/evaluations/{id}/results` |
| Visualización de imagen | Solicitud adicional `GET /api/v1/evaluations/{id}/retinography/image` |
| Versión integrada | Rama `Build/Integration-US16-FrontendSprint3`, commit `e5699e0`, publicada en `origin` |
| Datos de prueba | Evaluaciones existentes 1 y 2 con análisis; evaluación 3 creada sin retinografía ni análisis; identificador inexistente 999999999 |
| Evidencia de persistencia | F5 y consulta GET `200 OK` para evaluación 2; información reapareció después de reiniciar FastAPI y Angular |

Las pruebas HTTP se observaron en Chrome DevTools → **Network / Fetch-XHR**, seleccionando la solicitud `/results`. La prueba de prioridad MEDIA fue ejecutada mediante aserciones Python directamente sobre `calculate_suggested_priority()`; no se insertaron resultados artificiales en la base de datos.

## 3. Matriz resumida de pruebas

| ID | Escenario | Resultado esperado | Resultado observado | Veredicto |
|---|---|---|---|---|
| US16-T01 | Evaluación 2 con análisis almacenado | GET `200`; RD moderada; glaucoma alto riesgo; prioridad ALTA | HTTP `200 OK`, análisis 14, prioridad ALTA, advertencias visibles | **APROBADO** |
| US16-T02 | Evaluación 1 con análisis almacenado | RD sin indicios; glaucoma bajo riesgo; prioridad BAJA | Resultados y prioridad BAJA visibles | **APROBADO (visual)** |
| US16-T03 | Recarga F5 de evaluación 2 | Mantener resultados obtenidos del backend | Se repitió GET `200` y la información siguió visible | **APROBADO** |
| US16-T04 | Identificador inexistente 999999999 | GET `/results` → `404`; mensaje claro en Angular | `404 Not Found`; «La evaluación retiniana no fue encontrada.» | **APROBADO** |
| US16-T05 | Evaluación 3 sin análisis | GET `/results` → `409`; ausencia de resultados | `409 Conflict`; «Los resultados todavía no están disponibles.» | **APROBADO** |
| US16-T06 | Reglas de prioridad, cinco casos | BAJA / MEDIA / ALTA / ALTA / `None` | 5 aserciones Python correctas | **APROBADO (unitario/manual)** |
| US16-T07 | «Finalizar evaluación» de evaluación 2 | Regresar a ficha del paciente | Navega a `/patients/1`; el método solo llama a `router.navigate()` | **APROBADO (navegación)** |
| US16-T08 | Reiniciar servidores | FastAPI y Angular vuelven a cargar la aplicación | Ambos iniciaron; sesión y resultados de eval. 2 accesibles | **APROBADO (operación local)** |
| US16-T09 | Integración Git | Merge resuelto, árbol limpio, push exitoso | Commit `e5699e0` y rama remota creada | **APROBADO** |
| US16-T10 | Prioridad MEDIA desde GET en Angular | Recuperar caso MEDIA persistido y visualizarlo | No se dispone de evaluación real con ese resultado | **PENDIENTE (E2E)** |

## 4. Registro detallado de resultados

### US16-T01 / T03 — Recuperación persistida, evaluación 2

1. Acceder a `http://localhost:4200/evaluations/2/results` con sesión institucional activa.
2. Inspeccionar `GET http://127.0.0.1:8000/api/v1/evaluations/2/results` en Network.
3. Verificar `200 OK`, `id_evaluacion = 2`, `id_analisis = 14`, `estado = COMPLETADO`, `prioridad_sugerida = ALTA`, `requiere_revision = true`.
4. Comprobar la visualización de RD **Moderada (39,37 %)**, glaucoma **Alto riesgo (3,67 %)** y ambas advertencias de revisión.
5. Presionar **F5**; los resultados y la imagen reaparecen. La observación de la solicitud GET demuestra recuperación desde la API, no solo desde memoria temporal del frontend.

**Evidencias:** [Prioridad ALTA](evidencias/01_prioridad_alta.png), [GET 200](evidencias/03_get_200.png), [respuesta JSON](evidencias/04_json_resultados.png).

### US16-T02 — Prioridad BAJA, evaluación 1

Abrir `http://localhost:4200/evaluations/1/results`. Se observa RD **Sin indicios de Retinopatía Diabética (99,23 %)**, glaucoma **Bajo riesgo de Glaucoma (58,12 %)** y **prioridad sugerida BAJA**. La pantalla no utiliza una prioridad ALTA fija.

**Evidencia:** [Prioridad BAJA](evidencias/02_prioridad_baja.png). *La inspección Network explícita se documentó para la evaluación 2, no se repitió en esta captura.*

### US16-T04 — Evaluación inexistente

Abrir `http://localhost:4200/evaluations/999999999/results`; consultar en Network la solicitud `/results`. Respuesta observada **404 Not Found**; Angular presenta **«La evaluación retiniana no fue encontrada.»**. Otras solicitudes de detalle e imagen también pueden devolver 404 porque la evaluación no existe.

**Evidencia:** [HTTP 404](evidencias/05_http_404.png).

### US16-T05 — Evaluación existente sin análisis

Se creó la **evaluación 3** con médico de prueba existente y sin subir retinografía. Se abrió `http://localhost:4200/evaluations/3/results`; la petición `/results` devolvió **409 Conflict** y Angular mostró **«Los resultados todavía no están disponibles.»**. La solicitud separada de imagen devolvió **404** por ausencia de retinografía; esto no altera el veredicto del GET `/results`.

**Evidencia:** [HTTP 409](evidencias/06_http_409.png).

### US16-T06 — Casos de cálculo de prioridad

Se invocó `app.services.clinical_priority_service.calculate_suggested_priority()` usando aserciones Python sin consultar ni modificar PostgreSQL:

| Resultado RD | Resultado glaucoma | Esperado | Obtenido |
|---|---|---|---|
| Sin indicios de Retinopatía Diabética | Bajo riesgo de Glaucoma | BAJA | BAJA |
| Moderada | Bajo riesgo de Glaucoma | **MEDIA** | **MEDIA** |
| Moderada | Alto riesgo de Glaucoma | ALTA | ALTA |
| Severa | Bajo riesgo de Glaucoma | ALTA | ALTA |
| Moderada | `None` | `None` | `None` |

La función escoge la prioridad de mayor nivel entre ambos modelos, siempre que ambas categorías estén reconocidas. Las reglas usadas son **propuestas experimentales de soporte clínico**, no umbrales clínicamente validados.

### US16-T07 / T08 / T09 — Navegación, reinicio y Git

- **Finalizar evaluación:** el HTML enlaza `(click)="goToPatient()"`; el método `goToPatient()` navega a `/patients/{id}`. Se comprobó que desde la evaluación 2 dirige a `/patients/1`. **No se probó ni se implementó aquí un cierre transaccional en PostgreSQL.**
- **Reinicio local:** se detuvieron FastAPI y Angular con Ctrl+C y se reiniciaron. FastAPI mostró `Application startup complete` y GET `/` → `200 OK`; Angular inició correctamente. Los resultados de la evaluación 2 seguían visibles. **Incidencia menor:** una terminal mostró `conda: command not found`, aunque `python` ejecutó Uvicorn; conviene documentar cómo inicializar el entorno en terminales nuevas.
- **Git:** el merge terminó sin conflictos pendientes; `git diff --check` y `git diff --cached --check` no reportaron problemas. `git push -u origin Build/Integration-US16-FrontendSprint3` publicó la rama, con commit `e5699e0`. La revisión de compilación Angular en configuración de desarrollo y producción se realizó previamente; no constituye una batería automatizada de regresión.

## 5. Hallazgos y trabajo pendiente

| Prioridad de seguimiento | Hallazgo / límite observado | Acción propuesta |
|---|---|---|
| Alta, definición funcional | El botón «Finalizar evaluación» **solo navega**; no realiza cierre formal | Definir criterios de finalización, validaciones y endpoint de persistencia antes de cambiar comportamiento |
| Alta, consistencia de datos | En la tabla `evaluacion_retiniana`, las evaluaciones 1 y 2 mostraban `PENDIENTE` a pesar de poseer análisis IA completados | Acordar estados de evaluación vs. análisis vs. retinografía; evitar cambiar manualmente registros |
| Alta, rigor clínico | Prioridades ALTA/MEDIA/BAJA son una **regla experimental sin validación médica** | Validar criterios con oftalmólogos y ajustar términos/documentación antes de uso real |
| Media, prueba pendiente | MEDIA comprobada en Python, pero **no** observada en un análisis persistido a través de Angular | Preparar evaluación sintética/controlada sin alterar registros existentes; probar API y UI |
| Media, frontend | Botón «Ver» del historial de evaluaciones sin navegación implementada | Desarrollarlo coordinadamente con la responsable del frontend; el cambio provisional fue revertido |
| Media, experiencia de usuario | En escenarios 404/409 pueden verse solicitudes de imagen 404 y un botón de retorno sin estilos homogéneos | Evitar solicitar imagen si falta evaluación/retinografía y unificar estados vacíos/estilos |
| Media, semántica de IA | El indicador de confianza del glaucoma mostrado como 3,67 % en un caso de alto riesgo puede malinterpretarse como probabilidad clínica | Documentar significado y calibración del indicador; revisar el texto del frontend con especialistas |
| Media, cobertura de pruebas | No se verificaron 401/403, otros errores ni privacidad/autorización por establecimiento | Añadir pruebas de control de acceso y manejo de errores con cuentas de prueba independientes |
| Baja, entorno | En una terminal nueva se observó `conda: command not found`; el backend inició de todos modos | Verificar instalación/inicialización de Conda para reproducir el entorno |
| Baja, configuración | `angular.json` elevó presupuesto de error CSS de 8 kB a 10 kB para compilar | Registrar advertencias y optimizar estilos en una tarea posterior |

## 6. Incidencia adicional de otro entorno (resuelta)

En el equipo de otra integrante, la interfaz indicó **«Los modelos de inteligencia artificial no están configurados correctamente»**. La consulta a la tabla `modelo_ia` reveló que no había registros. Se identificó `retina-support-backend/app/scripts/seed_ai_models.py`, que registra `EfficientNetB3+SE` para RD y `ResNet50V2` para glaucoma; la integrante confirmó que el problema se resolvió ejecutando el script. **Este incidente es de configuración de un entorno distinto y no constituye una prueba de desempeño ni de calidad diagnóstica de los modelos.**

## 7. Recomendaciones de cierre y reproducción

1. Conservar el commit de integración `e5699e0` como línea base de esta evidencia. Si se agrega este informe al repositorio, generar **un commit nuevo de documentación**, sin modificar el commit ya publicado.
2. Mantener las evaluaciones 1 y 2 como evidencia de ALTA/BAJA. La evaluación 3 fue creada únicamente para comprobar el error 409; no borrarla ni analizarla hasta acordar la política de datos de prueba.
3. Para repetir una consulta: iniciar PostgreSQL, FastAPI y Angular; acceder con cuenta institucional de prueba; abrir `/evaluations/2/results`; recargar; verificar `GET /api/v1/evaluations/2/results` → 200 y `prioridad_sugerida = "ALTA"`.
4. Para reproducir 404 y 409: consultar `/evaluations/999999999/results` y `/evaluations/3/results` respectivamente, solo mientras esos identificadores sigan siendo válidos en la base de pruebas.
5. No utilizar la regla de prioridad ni los porcentajes de confianza como recomendaciones diagnósticas autónomas o criterios de urgencia clínica sin validación de especialistas.

## 8. Índice de evidencias recortadas

- `evidencias/01_prioridad_alta.png`: resultados RD/glaucoma y prioridad ALTA.
- `evidencias/02_prioridad_baja.png`: resultados RD/glaucoma y prioridad BAJA.
- `evidencias/03_get_200.png`: GET `/evaluations/2/results` → `200 OK`.
- `evidencias/04_json_resultados.png`: campos JSON del resultado persistido y alertas.
- `evidencias/05_http_404.png`: GET de evaluación inexistente → `404 Not Found`.
- `evidencias/06_http_409.png`: GET de evaluación existente sin análisis → `409 Conflict`.

*Fuente del informe: pruebas manuales, salidas de comandos, código mostrado y capturas aportadas durante la sesión de integración del 14/11/2026. No se atribuyen métricas de rendimiento ni conclusiones clínicas que no hayan sido verificadas.*
