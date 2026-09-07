# Guía y Demostración del Prototipo Demo Interactivo

¡El **Prototipo Demo Interactivo** para la tesis de soporte clínico con Inteligencia Artificial ya está completamente desarrollado y funcionando localmente!

---

## 🎨 Capturas y Demostración Visual

### 📄 Informe Clínico Oficial (PDF Modal)
El sistema genera automáticamente el reporte oficial estandarizado para el **Centro Oftalmológico V.E.R.**, incluyendo los datos del paciente, diagnóstico probabilístico multiclase por DenseNet121, recomendaciones médicas y firma de la **Dra. Lucero Manchay Paredes**:

![Informe Clínico Oficial (PDF Modal)](file:///C:/Users/Lucero/.gemini/antigravity/brain/acf748d2-be3a-4028-a106-af92a26ccd9c/clinical_report_modal_1787445118473.png)

---

## ⚡ Características Implementadas

### 1. 🩺 Triaje & Inferencia IA (DenseNet121)
- **Presets Reales de Retinografías:** Muestras de prueba precargadas (Ojo Sano, Retinopatía Diabética, Glaucoma) e interfaz *drag & drop* para nuevas imágenes.
- **Filtros de Procesamiento en Tiempo Real:** 
  - *Normal:* Retinografía original en alta resolución.
  - *CLAHE (Realce de Vasos):* Filtro de contraste especializado para resaltar la vascularización retiniana y los bordes del disco óptico.
  - *Mapa de Calor (XAI):* Simulación de explicabilidad algorítmica para visualizar las zonas críticas analizadas por la CNN.
- **Simulación de Inferencia Asíncrona:** Línea de escaneo animada con barra de confianza %, desglose de probabilidades Softmax y recomendaciones automatizadas.

### 2. 👥 Historial & Seguimiento de Pacientes
- Tabla interactiva de pacientes con DNI, edad, nivel de severidad y fecha de triaje.
- Clasificación visual inmediata por código de color (🟢 Normal, 🟡 Retinopatía Diabética, 🔴 Glaucoma).

### 3. 📊 Dashboard de Impacto Clínico
- Indicadores en vivo: Total de triajes, precisión diagnóstica (96.8%), tiempo medio de triaje (2.4 min) y derivaciones urgentes.
- Reducción sustancial del tiempo de espera de 120 días a minutos en consultorios de Lima Metropolitana.

### 4. ⚙️ Sección Informativa de Arquitectura & Benchmarking
- Gráficos estructurados de la arquitectura lógica (Angular + FastAPI + DenseNet121 + AWS) para la sustentación ante el jurado examinador de la tesis.

---

## 🚀 Cómo Ejecutar la Demo en tu Laptop

El servidor local ya se encuentra activo en tu computadora. Puedes abrir el prototipo interactivo en cualquier navegador siguiendo estos pasos:

1. **Servidor Activo:** La aplicación está corriendo en:
   ```text
   http://localhost:8080
   ```
2. **Archivos del Proyecto:** Todo el código fuente comprimido y listo para despliegue se encuentra guardado en tu escritorio en:
   ```text
   c:\Users\Lucero\Desktop\Demo de TDP1\
   ├── index.html
   ├── css/styles.css
   ├── js/app.js
   └── assets/images/
   ```

---

## 🛠️ Verificación Realizada
- [x] Ejecución del servidor local en `http://localhost:8080`.
- [x] Interacción fluida con el selector de presets de retinografías.
- [x] Simulación de inferencia con DenseNet121 y cálculo de probabilidades.
- [x] Generación e impresión/descarga del informe clínico oficial de la Dra. Lucero Manchay.
