# Plan de Diseño e Implementación del Prototipo Demo Interactivo

Este plan establece el diseño técnico, la estructura de interfaz y el flujo funcional para la creación del **Prototipo Demo Interactivo** de la tesis: *“Aplicación Web de Soporte Clínico basada en Redes Neuronales Convolucionales para la Identificación Automatizada de Patologías Retinianas en Consultorios de Lima Metropolitana”*.

El objetivo es construir un prototipo web con calidad visual de nivel producción (estética médica futurista y moderna), que permita simular el flujo clínico completo en tiempo real tanto para sustentaciones académicas como para pruebas con usuarios.

---

## 🎯 Alcance del Prototipo / Demo

El prototipo representará la propuesta técnica aprobada en el informe de investigación y el benchmarking (**DenseNet121 + FastAPI + Angular**), ofreciendo una experiencia interactiva completa:

### 1. Módulo de Triaje & Inferencia de Inteligencia Artificial (DenseNet121)
- **Carga de Retinografías:** Área *drag & drop* y selector de imágenes preset reales de prueba (Glaucoma, Retinopatía Diabética, Ojo Sano).
- **Preprocesamiento en Tiempo Real:** Visualización del aislamiento de Región de Interés (ROI), normalización y filtro CLAHE (mejora de contraste de vasos sanguíneos y disco óptico).
- **Motor de Inferencia Asíncrona:** Simulación con latencia realista (<1.2s), visualizador de confianza diagnóstica %, desglose de probabilidades por patología y nivel de severidad.
- **Explicabilidad de IA (XAI / Heatmaps):** Simulación de mapa de atención sobre el fondo de ojo destacando excavación de copa óptica (Glaucoma) o exudados/microaneurismas (Retinopatía Diabética).

### 2. Módulo de Gestión de Pacientes & Historial Longitudinal
- Registro de pacientes simulados en consultorio (DNI, Nombres, Edad, Historial Clínico).
- Trazabilidad de evaluaciones pasadas y comparación evolutiva de patologías en el tiempo.

### 3. Módulo de Informe Clínico Digital PDF
- Generación instantánea en pantalla de reporte clínico oficial listo para imprimir o guardar.
- Incluye: datos del paciente, imagen procesada, diagnóstico predictivo de IA con % de confianza, espacio para validación/firma del especialista oftalmólogo e indicaciones médicas.

### 4. Dashboard de Indicadores Clínicos y Eficiencia
- Métricas en vivo de triaje: Reducción de tiempo de atención (de 120 días a minutos), distribución de diagnósticos, tasa de derivación a especialidad.

### 5. Sección Informativa de Arquitectura y Benchmarking (Modo Sustentación)
- Vista explicativa de la arquitectura lógica (Angular + FastAPI + DenseNet121 + AWS) y matriz de decisiones tecnológicas del benchmarking para demostración ante jurados de tesis.

---

## 🎨 Diseño Estético y UI/UX

- **Paleta de Colores:** Mapeo de interfaz médica *Deep Clinical Dark & Slate Modern*:
  - Fondo Principal: `#0A0F1D` / `#111827`
  - Contenedores / Glassmorphism: `rgba(30, 41, 59, 0.7)` con bordes cibernéticos `#38BDF8`
  - Acentos de Diagnóstico:
    - 🟢 Sano: `#10B981` (Verde Esmeralda)
    - 🟡 Retinopatía Diabética: `#F59E0B` (Ámbar Clínico)
    - 🔴 Glaucoma: `#EF4444` (Rojo Coral)
- **Tipografía:** Google Fonts (`Inter` para legibilidad clínica y `Outfit` para títulos y métricas).
- **Micro-animaciones:** Transiciones fluidas en escaneo de retina, animaciones en barras de progreso de confianza y tarjetas colapsables.

---

## 🏗️ Propuesta de Componentes del Prototipo

```
c:\Users\Lucero\Desktop\Demo de TDP1\
├── index.html                  # Aplicación SPA principal
├── css/
│   └── styles.css              # Sistema de diseño, tokens, glassmorphism y animaciones
├── js/
│   ├── app.js                  # Orquestador del flujo, cambio de pestañas y modales
│   ├── ai_engine.js            # Motor de simulación DenseNet121, preprocesamiento y grad-CAM
│   ├── patient_manager.js      # Gestión de historial clínico e imágenes
│   └── pdf_generator.js        # Generador de informes clínicos imprimibles/descargables
└── assets/
    ├── images/                 # Muestras de retinografías de alta resolución
    └── icons/                  # Iconografía clínica SVG
```

---

## 🧪 Plan de Verificación

### Pruebas Funcionales Interactivas
1. **Flujo de Triaje Completo:** Cargar/Seleccionar imagen de prueba $\rightarrow$ Ejecutar inferencia $\rightarrow$ Verificar resultados de DenseNet121 (Probabilidad + Heatmap) $\rightarrow$ Generar informe clínico.
2. **Prueba de Pacientes:** Filtrar historial por DNI/Patología y ver gráfico evolutivo de seguimiento.
3. **Generación de Reporte:** Probar previsualización del informe PDF en ventana modal e impresión.
4. **Responsiad y Rendimiento:** Probar interacción fluida en pantalla completa y dispositivos móviles/tablets.

---

## ❓ Preguntas para el Usuario

> [!NOTE]
> 1. ¿Deseas que incluyamos algún consultorio u hospital específico en el encabezado de los informes clínicos (ej: *Centro Oftalmológico V.E.R.* o *INO*)?
> 2. ¿Te parece bien que compilemos toda la demo interactiva en una aplicación web autónoma ejecutable localmente para que puedas presentarla fácilmente en tu laptop o subirla a internet?
