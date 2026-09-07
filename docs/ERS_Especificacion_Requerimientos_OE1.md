# ESPECIFICACIÓN DE REQUERIMIENTOS DEL SISTEMA (ERS / SRS)

**Proyecto:** RetiScan — Aplicación Web de Soporte Clínico basada en Redes Neuronales Convolucionales para la Identificación Automatizada de Patologías Retinianas en Consultorios de Lima Metropolitana  
**Institución:** Universidad Peruana de Ciencias Aplicadas (UPC) — Facultad de Ingeniería — Ciencias de la Computación  
**Caso de Estudio:** Centro Oftalmológico V.E.R. (Lima Metropolitana)  
**Estándar de Referencia:** IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018  
**Entregable Académico:** Objetivo Específico 1 — Indicador OE1-I1  
**Autores:** José Antonio Mayhua Hinostroza | Lucero Salome Manchay Paredes  
**Asesor:** Pedro Segundo Castañeda Vargas  
**Fecha:** Septiembre de 2026  
**Versión:** 1.0  

---

## 1. INTRODUCCIÓN

### 1.1 Propósito del Documento
El presente documento tiene como objetivo formalizar la especificación completa de requerimientos funcionales y no funcionales para el desarrollo del sistema **RetiScan**. Esta especificación sirve como base contractual y técnica para el diseño arquitectónico, el entrenamiento algorítmico, la implementación del software y la posterior fase de validación clínica simulada, en cumplimiento del **Objetivo Específico 1 (OE1)** del proyecto de titulación.

### 1.2 Alcance del Producto
RetiScan es una solución de software web orientada al soporte del diagnóstico clínico (CAD - *Computer-Aided Diagnosis*). Su función primordial es clasificar automáticamente imágenes de fondo de ojo (retinografías) no midriáticas en tres categorías clínicas:
1. **Sin Hallazgos Patológicos (Ojo Sano / Normal)**.
2. **Retinopatía Diabética (RD)** en sus distintos grados de severidad vascular.
3. **Glaucoma (G)** caracterizado por incremento patológico de la relación copa-disco (*CDR > 0.65*).

> [!IMPORTANT]
> **Delimitación de Responsabilidad Clínica:** RetiScan constituye una herramienta de asistencia al triaje y segunda opinión diagnóstica. El sistema **no reemplaza** el criterio clínico ni la evaluación oftalmológica definitiva del médico especialista responsable.

### 1.3 Personal y Actores Involucrados
* **Médico Oftalmólogo / Retinólogo:** Usuario clínico primario que analiza las alertas probabilísticas generadas por la IA, inspecciona las retinografías con realce vascular (CLAHE) y mapas de explicabilidad (XAI), valida el diagnóstico y emite el informe médico digital formal.
* **Personal Técnico / Optometrista:** Usuario operativo encargado de capturar las imágenes con el retinógrafo, ingresarlas al sistema, verificar la calidad de imagen y registrar los datos demográficos básicos del paciente.
* **Administrador del Sistema:** Rol responsable de la gestión de credenciales, auditoría de accesos y supervisión de los indicadores globales de triaje.

### 1.4 Marco Normativo y Legal Aplicable
1. **Ley N.° 29733 — Ley de Protección de Datos Personales (Perú):** Tratamiento confidencial de datos sensibles de salud. Toda imagen y registro clínico debe ser procesado de manera disociada/anonimizada en entornos de prueba y almacenamiento cloud.
2. **Decreto Supremo N.° 003-2013-JUS:** Reglamento de la Ley de Protección de Datos Personales en materia de medidas de seguridad técnicas y organizativas para bancos de datos personales.
3. **Ley N.° 31814 — Ley que promueve el uso de la Inteligencia Artificial en favor del desarrollo económico y social del país:** Exigencia de principios éticos, transparencia algorítmica, supervisión humana continua (*Human-in-the-loop*) y no discriminación por sesgos demográficos en soluciones basadas en IA.
4. **Ley N.° 30096 — Ley de Delitos Informáticos:** Protección de la integridad de los sistemas, bases de datos y comunicaciones telemáticas.
5. **Ley N.° 30024 — Ley que crea el Registro Nacional de Historias Clínicas Electrónicas (RENHICE):** Estandarización de metadatos clínicos y trazabilidad longitudinal.

---

## 2. MODELADO DEL PROCESO CLÍNICO (AS-IS vs. TO-BE)

### 2.1 Flujo Clínico Actual (As-Is)
En los consultorios oftalmológicos tradicionales de Lima Metropolitana, el flujo de atención presenta severas deficiencias operativas:
1. El paciente acude a consulta general o triaje primario con síntomas inespecíficos o control rutinario de diabetes.
2. Si se sospecha daño retiniano, es derivado a la toma de retinografía. La imagen es almacenada localmente en la memoria del retinógrafo o en discos duros locales desarticulados.
3. El paciente debe esperar entre **45 y 120 días** para obtener una cita de lectura con el único especialista en retina o glaucoma disponible.
4. El oftalmólogo realiza una inspección visual manual no asistida, con alta carga cognitiva y variabilidad inter-observador.
5. Si el paciente padecía retinopatía proliferativa o glaucoma de ángulo abierto avanzado, el retraso genera daño irreversible en las fibras nerviosas o ceguera prevenible.

### 2.2 Flujo Clínico Propuesto con RetiScan (To-Be)
Con la implementación de la plataforma CAD web:
1. El técnico captura la retinografía no midriática y la carga en RetiScan vía navegador web.
2. El backend aplica de forma instantánea preprocesamiento (aislamiento de ROI, filtro CLAHE y normalización).
3. El motor de inferencia asíncrono con **DenseNet121** clasifica la imagen en menos de **1.5 segundos**, generando un vector de probabilidades Softmax y activando el mapa de atención explicable.
4. **Clasificación de Riesgo Inmediata:**
   * Si detecta alta sospecha de patología, el sistema asigna prioridad **Urgente (< 5 días)** o **Alta (< 7 días)**, alertando al especialista en su bandeja de triaje.
   * Si no presenta hallazgos patológicos, se programa control rutinario en 12 meses.
5. El oftalmólogo revisa la alerta, confirma o ajusta el criterio, y genera con un clic el **Informe Clínico Oficial en PDF**, firmado digitalmente y respaldado en la nube.

```
FLUXOGRAMA DEL PROCESO TO-BE (RETISCAN)
[Paciente] ──> [Captura Retinógrafo] ──> [Técnico carga imagen a RetiScan]
                                                      │
                                                      ▼
                                          [Preprocesamiento OpenCV]
                                          (ROI + CLAHE + 224x224)
                                                      │
                                                      ▼
                                          [Inferencia DenseNet121]
                                          (Vector de Confianza %)
                                                      │
                                                      ▼
                                          [Bandeja de Triaje Médico]
                                                      │
                      ┌───────────────────────────────┴───────────────────────────────┐
                      ▼                                                               ▼
           [Patología Detectada]                                              [Sin Hallazgos]
      (Prioridad Alta/Urgente <7 días)                                     (Control Rutinario 12m)
                      │                                                               │
                      └───────────────────────────────┬───────────────────────────────┘
                                                      ▼
                                          [Validación Oftalmólogo]
                                                      │
                                                      ▼
                                      [Generación Reporte Clínico PDF]
                                                      │
                                                      ▼
                                       [Persistencia AWS S3 / Postgres]
```

---

## 3. ESPECIFICACIÓN DE REQUERIMIENTOS FUNCIONALES (RF)

Los requerimientos funcionales se agrupan en las 7 épicas aprobadas en el alcance del proyecto:

### Épica 01: Gestión de Acceso, Autenticación y Roles (EP01)
* **RF-01 (Autenticación Segura):** El sistema debe permitir el inicio de sesión de usuarios mediante credenciales únicas (correo y contraseña cifrada con bcrypt), generando un token de sesión JWT con tiempo de expiración configurable.
* **RF-02 (Control de Acceso Basado en Roles - RBAC):** El sistema debe restringir las vistas y acciones según el rol asignado:
  * *Técnico:* Registro de pacientes, carga de retinografías y visualización de estado de carga.
  * *Médico Oftalmólogo:* Visualización de probabilidades, mapas de calor, registro de observaciones clínicas, validación diagnóstica y emisión de informes PDF.
  * *Administrador:* Gestión de usuarios, métricas de auditoría y configuración de parámetros.
* **RF-03 (Cierre de Sesión e Inactividad):** El sistema debe revocar el token JWT al cerrar sesión o tras 15 minutos de inactividad del usuario.
* **RF-04 (Auditoría de Acciones):** El sistema debe registrar un log de auditoría inmutable de cada consulta o modificación de registros clínicos con fecha, hora y usuario responsable.

### Épica 02: Gestión de Pacientes y Búsqueda Clínica (EP02)
* **RF-05 (Registro Demográfico del Paciente):** El sistema debe permitir registrar nuevos pacientes capturando: DNI/Carné de Extranjería, Nombres, Apellidos, Fecha de Nacimiento, Sexo, Antecedentes de Diabetes Mellitus (Sí/No, Años de evolución) e Historial de Hipertensión Arterial.
* **RF-06 (Búsqueda Ágil de Pacientes):** El sistema debe permitir buscar expedientes clínicos por número de DNI o nombres/apellidos en tiempo real con una latencia inferior a 500 ms.
* **RF-07 (Validación de Documento de Identidad):** El sistema debe validar el formato del DNI peruano (8 dígitos numéricos válidos) antes de permitir el registro.
* **RF-08 (Historial Longitudinal de Evaluaciones):** El sistema debe presentar una vista cronológica de todas las retinografías y evaluaciones previas del paciente seleccionado, permitiendo comparar visualmente la progresión en el tiempo.

### Épica 03: Registro de Evaluación y Carga de Retinografías (EP03)
* **RF-09 (Carga Multiformato):** El sistema debe permitir la carga de imágenes de fondo de ojo en formatos JPG, JPEG y PNG mediante un área interactiva de arrastrar y soltar (*drag & drop*) o explorador de archivos.
* **RF-10 (Asignación de Lateralidad Ocular):** El sistema debe exigir la especificación del ojo evaluado: Ojo Derecho (OD) u Ojo Izquierdo (OS) para cada imagen cargada.
* **RF-11 (Validación de Integridad y Tamaño):** El sistema debe validar que el archivo cargado no supere los 15 MB de peso y cuente con una resolución mínima de $512 \times 512$ píxeles.
* **RF-12 (Control de Calidad de Ingesta):** El sistema debe rechazar archivos corruptos o imágenes que no presenten estructura cromática compatible con fondo de ojo (evitando cargas accidentales de documentos ajenos).

### Épica 04: Preprocesamiento Automático de Imágenes (EP04)
* **RF-13 (Aislamiento Automático de ROI):** El sistema debe segmentar automáticamente el área retiniana circular útil, eliminando los márgenes negros laterales y centrando la imagen en un recuadro cuadrado sin deformación anatómica.
* **RF-14 (Filtro Adaptativo CLAHE):** El sistema debe aplicar ecualización adaptativa de histograma con límite de contraste (CLAHE en espacio de color LAB/canal L con `clipLimit=2.0` y grilla $8 \times 8$) para balancear la luminosidad y resaltar la red vascular retiniana.
* **RF-15 (Estandarización Dimensional):** El sistema debe redimensionar la imagen preprocesada a una matriz cuadrada de $224 \times 224 \times 3$ mediante interpolación bicúbica.
* **RF-16 (Normalización Numérica de Píxeles):** El sistema debe transformar la matriz de píxeles a valores de punto flotante en el rango cerrado $[0.0, 1.0]$ antes de enviarla al grafo computacional del modelo.

### Épica 05: Inferencia con Modelo CNN y Resultados Diagnósticos (EP05)
* **RF-17 (Inferencia Asíncrona con DenseNet121):** El sistema debe despachar la retinografía preprocesada al servicio de inferencia de DenseNet121 de manera no bloqueante para la interfaz de usuario.
* **RF-18 (Cálculo Probabilístico Multiclase):** El sistema debe obtener del modelo la distribución de probabilidad (función Softmax) desglosada para las tres clases objetivo:
  * Probabilidad de Sin Hallazgos Patológicos (Sano).
  * Probabilidad de Retinopatía Diabética.
  * Probabilidad de Glaucoma.
* **RF-19 (Determinación de Confianza Diagnóstica):** El sistema debe identificar la clase predictiva dominante y reportar su porcentaje de certeza diagnóstica (ej: 96.4%).
* **RF-20 (Simulación y Visualización de Mapa de Calor XAI):** El sistema debe proyectar sobre el fondo de ojo una máscara de explicabilidad (mapa de calor tipo Grad-CAM) que resalte las regiones de mayor activación convolucional (disco óptico para glaucoma, microvasos/exudados para retinopatía).

### Épica 06: Soporte al Triaje Visual, Historial y Reportes PDF (EP06)
* **RF-21 (Categorización de Prioridad de Atención):** El sistema debe clasificar automáticamente el nivel de atención según la patología detectada:
  * *Urgente (< 5 días):* Sospecha de Glaucoma o Retinopatía Proliferativa / Excavación severa.
  * *Alta (< 7 días):* Sospecha de Retinopatía Diabética No Proliferativa Moderada.
  * *Rutinaria (12 meses):* Ausencia de hallazgos patológicos.
* **RF-22 (Recomendaciones Clínicas Sugeridas):** El sistema debe desplegar recomendaciones clínicas preliminares basadas en guías oftalmológicas estandarizadas según la predicción obtenida.
* **RF-23 (Anotaciones y Validación del Especialista):** El sistema debe proveer un campo de texto estructurado para que el médico oftalmólogo confirme, rectifique o complemente el diagnóstico automatizado antes del cierre del triaje.
* **RF-24 (Generación de Informe Clínico Digital PDF):** El sistema debe compilar un documento PDF oficial con membrete del Centro Oftalmológico V.E.R. que incluya:
  * Identificador único de informe (`#INF-YYYY-XXXX`) y fecha.
  * Datos completos del paciente (DNI, edad, sexo, antecedentes).
  * Retinografía original y retinografía procesada.
  * Diagnóstico sugerido por IA con su desglose probabilístico y recomendación.
  * Diagnóstico médico definitivo y observaciones del especialista.
  * Datos colegiados del médico tratante (Nombre, CMP, RNE) y casillero de firma digital.
* **RF-25 (Descarga e Impresión):** El sistema debe permitir la visualización previa en modal y la descarga o impresión directa del informe PDF generado.

### Épica 07: Dashboard de Indicadores y Auditoría del Prototipo (EP07)
* **RF-26 (Métricas Operativas en Tiempo Real):** El sistema debe presentar un panel analítico con los siguientes KPIs:
  * Total de triajes realizados en el período.
  * Exactitud global estimada del modelo en validación.
  * Tiempo promedio de triaje por paciente (en minutos).
  * Conteo de casos derivados con prioridad Urgente/Alta.
* **RF-27 (Distribución Epidemiológica):** El sistema debe mostrar un gráfico de torta/barras con la proporción de pacientes sanos vs. con retinopatía diabética vs. con glaucoma evaluados en el consultorio.
* **RF-28 (Exportación de Métricas):** El sistema debe permitir la exportación de las estadísticas acumuladas en formato tabular (CSV / Excel) para fines de control de gestión.

---

## 4. ESPECIFICACIÓN DE REQUERIMIENTOS NO FUNCIONALES (RNF) SEGÚN ISO/IEC 25010

| Código | Dimensión de Calidad | Especificación del Requerimiento | Métrica / Criterio de Aceptación |
| :--- | :--- | :--- | :--- |
| **RNF-01** | Rendimiento (Tiempo de Inferencia) | El tiempo transcurrido desde el inicio del envío de la imagen hasta la obtención del vector probabilístico del modelo DenseNet121 no debe exceder de 2.0 segundos en el servidor de pruebas. | $\le 2.0$ segundos bajo concurrencia estándar. |
| **RNF-02** | Rendimiento (Tiempo de Carga UI) | La interfaz web debe responder a las transiciones de pestañas y carga de vistas en menos de 1.0 segundo. | $\le 1.0$ segundo de renderizado en cliente. |
| **RNF-03** | Seguridad (Cifrado de Canal) | Toda comunicación entre la interfaz de usuario, la API backend y los servicios cloud debe realizarse exclusivamente sobre el protocolo HTTPS con cifrado TLS 1.3. | 100% de peticiones sobre canal cifrado. |
| **RNF-04** | Seguridad (Anonimización de Datos) | Las imágenes de fondo de ojo utilizadas en almacenamiento y datasets no deben contener metadatos EXIF con nombres, fechas de nacimiento ni identificadores personales, cumpliendo con la Ley N.° 29733. | Metadatos personales = 0 en imágenes almacenadas. |
| **RNF-05** | Seguridad (Autenticación Robusta) | Las contraseñas de los usuarios deben almacenarse con función hash criptográfica irreversible (bcrypt con costo $\ge 12$). | Cero almacenamiento de contraseñas en texto plano. |
| **RNF-06** | Usabilidad (Facilidad de Aprendizaje) | La interfaz de usuario debe alcanzar un puntaje mínimo de 80 en la escala de usabilidad del sistema (*System Usability Scale - SUS*) en pruebas con usuarios clínicos. | Puntaje SUS $\ge 80 / 100$. |
| **RNF-07** | Accesibilidad Visual | La interfaz clínica debe respetar el contraste de color WCAG 2.1 nivel AA (mínimo 4.5:1 para texto normal) para asegurar legibilidad en ambientes de penumbra oftalmológica. | Ratio de contraste $\ge 4.5:1$. |
| **RNF-08** | Disponibilidad del Servicio | El prototipo desplegado en el entorno de pruebas cloud debe mantener una disponibilidad operativa mínima del 99.0% durante el período de evaluación técnica. | Uptime $\ge 99.0\%$. |
| **RNF-09** | Portabilidad y Compatibilidad | La aplicación web debe operar de forma consistente en los navegadores web modernos estándar (Google Chrome $\ge 115$, Mozilla Firefox $\ge 115$, Microsoft Edge $\ge 115$). | Cero errores de incompatibilidad en navegadores objetivo. |
| **RNF-10** | Mantenibilidad y Modularidad | El código fuente debe estructurarse separando estrictamente la capa de presentación (Frontend SPA), la API de servicios (Backend FastAPI) y los scripts de procesamiento IA (OpenCV/Keras). | Desacoplamiento total verificado mediante pruebas unitarias. |

---

## 5. MATRIZ DE HISTORIAS DE USUARIO REPRESENTATIVAS

### HU-01: Carga y Preprocesamiento de Retinografía
* **Como:** Personal técnico del Centro Oftalmológico V.E.R.
* **Quiero:** Cargar una retinografía no midriática y previsualizarla con recorte automático de bordes negros y realce de contraste.
* **Para:** Asegurar que la imagen sea nítida y apta antes de iniciar el análisis automatizado.
* **Criterios de Aceptación (Gherkin):**
  * *Dado* que el técnico ha iniciado sesión y seleccionado un paciente registrado,
  * *Cuando* arrastra un archivo JPG de fondo de ojo a la zona de carga,
  * *Entonces* el sistema valida que el formato y resolución sean correctos, recorta la región circular de la retina, aplica el filtro CLAHE y muestra la vista previa en el visor en menos de 2 segundos.

### HU-02: Ejecución de Inferencia y Obtención de Diagnóstico IA
* **Como:** Médico oftalmólogo tratante.
* **Quiero:** Ejecutar el modelo DenseNet121 sobre la retinografía y visualizar el desglose de probabilidades y la sospecha de patología.
* **Para:** Contar con una segunda opinión diagnóstica objetiva y priorizar la atención de casos con riesgo de ceguera.
* **Criterios de Aceptación (Gherkin):**
  * *Dado* que la retinografía preprocesada se encuentra visible en el visor clínico,
  * *Cuando* el médico presiona el botón "Ejecutar Inferencia de IA",
  * *Entonces* el sistema despliega una línea de escaneo temporal, consulta la API de inferencia y muestra las barras de probabilidad para Sano, Retinopatía Diabética y Glaucoma con su nivel de confianza y prioridad de derivación.

### HU-03: Emisión del Reporte Clínico Oficial en PDF
* **Como:** Médico oftalmólogo tratante.
* **Quiero:** Generar un informe clínico digital descargable en PDF con los resultados de la IA, mis indicaciones médicas y firma colegiada.
* **Para:** Entregar un respaldo formal al paciente e integrarlo al expediente clínico del Centro Oftalmológico V.E.R.
* **Criterios de Aceptación (Gherkin):**
  * *Dado* que la inferencia ha finalizado y el médico ha registrado sus indicaciones,
  * *Cuando* hace clic en "Generar Informe Clínico Oficial (PDF)",
  * *Entonces* se abre una ventana modal con el informe formateado a nivel institucional, incluyendo datos del paciente, imagen procesada, porcentajes de IA, credenciales médicas (CMP/RNE) y botón de descarga/impresión.

---

## 6. CONCLUSIÓN Y APROBACIÓN DEL ENTREGABLE OE1-I1
La presente Especificación de Requerimientos del Sistema (ERS) establece las directrices funcionales, arquitectónicas y normativas requeridas para el desarrollo e integración de los componentes de software e inteligencia artificial del proyecto RetiScan. 

El cumplimiento riguroso de estos requerimientos garantiza la trazabilidad clínica, la protección de los datos de salud bajo la legislación peruana y la optimización de los tiempos de triaje en consultorios oftalmológicos de Lima Metropolitana.
