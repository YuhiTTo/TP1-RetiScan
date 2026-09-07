# REPORTE TÉCNICO: PIPELINE DE DATOS Y PREPROCESAMIENTO DE RETINOGRAFÍAS

**Proyecto:** RetiScan — Aplicación Web de Soporte Clínico basada en CNN  
**Institución:** Universidad Peruana de Ciencias Aplicadas (UPC) — Ciencias de la Computación  
**Caso de Estudio:** Centro Oftalmológico V.E.R. (Lima Metropolitana)  
**Entregable Académico:** Objetivo Específico 1 — Indicador OE1-I2  
**Autores:** José Antonio Mayhua Hinostroza | Lucero Salome Manchay Paredes  
**Asesor:** Pedro Segundo Castañeda Vargas  
**Fecha:** Septiembre de 2026  
**Versión:** 1.0  

---

## 1. RESUMEN EJECUTIVO

El presente informe documenta el diseño, la fundamentación matemática y la implementación computacional del repositorio y pipeline de preparación de datos para el proyecto **RetiScan**, en cumplimiento del **Indicador OE1-I2**. 

El pipeline transforma retinografías no midriáticas crudas en tensores estandarizados, balanceados y optimizados para el posterior entrenamiento y evaluación de la red neuronal convolucional **DenseNet121** (OE2). La arquitectura del pipeline garantiza la reproducibilidad experimental, el aislamiento estricto de datos de evaluación (*Zero Data Leakage*) y la mitigación activa de sesgos demográficos mediante ecualización adaptativa local (**CLAHE**).

---

## 2. ESTRATEGIA DE MITIGACIÓN DE SESGOS Y FUENTES DE DATOS

### 2.1 El Problema del Sesgo Demográfico y Cambio de Dominio (*Domain Shift*)
En el análisis oftalmológico automatizado, la pigmentación del epitelio pigmentario de la retina y de la coroides varía sustancialmente según el origen étnico:
* **Población Caucásica:** Menor densidad de melanina, fondo retiniano de tonalidad naranja claro o amarillenta.
* **Población Hispanoamericana / Peruana:** Mayor densidad de melanina coroidea, generando patrones retinianos más oscuros (fondos "atigrados" o hiperpigmentados).
* **Morfología Papilar:** La población latinoamericana presenta con frecuencia excavaciones fisiológicas del disco óptico de mayor diámetro de forma natural, lo que en modelos no adaptados induce falsos positivos de Glaucoma.

### 2.2 Estrategia Metodológica en Dos Fases
Para abordar este reto sin detener el desarrollo por demoras en la entrega de muestras clínicas locales, el proyecto adopta una estrategia científicamente validada:

```
                  ESTRATEGIA METODOLÓGICA DE DATOS
┌──────────────────────────────────────────────┐
│  FASE 1: Pre-entrenamiento Global            │
│  (Datasets Públicos ODIR-5K / APTOS)         │
│  • Extracción de rasgos universales: vasos,  │
│    microaneurismas, excavación papilar.      │
│  • Alto volumen de imágenes de referencia.   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  FASE 2: Adaptación Local y Validación       │
│  (Centro Oftalmológico V.E.R. - Lima)        │
│  • Fine-tuning sobre capas densas.           │
│  • Validación externa en pacientes peruanos. │
│  • Evaluación de robustez ante sesgo local.  │
└──────────────────────────────────────────────┘
```

---

## 3. ESPECIFICACIÓN TÉCNICA DEL PIPELINE DE PREPROCESAMIENTO

El módulo implementado en [`scripts/preprocess.py`](file:///c:/Users/Lucero/Documents/TP1-RetiScan/scripts/preprocess.py) ejecuta cuatro transformaciones secuenciales:

```
[Retinografía Cruda] 
        │
        ▼ (1) Recorte Automático de ROI
[Retina Centrada sin Márgenes Negros]
        │
        ▼ (2) Filtro Adaptativo CLAHE (Canal L en espacio CIE LAB)
[Imagen con Contraste Microvascular Realzado]
        │
        ▼ (3) Redimensionamiento Bicúbico a 224 × 224
[Matriz Estandarizada]
        │
        ▼ (4) Normalización Numérica en [0.0, 1.0]
[Tensor Optimizado para DenseNet121]
```

### 3.1 Detección y Recorte de la Región de Interés (ROI)
Las cámaras de retinografía producen imágenes con amplios márgenes negros circundantes que no contienen información clínica y desperdician capacidad representacional de la CNN.
* **Algoritmo:**
  1. Conversión de la imagen a escala de grises $I_{gray}(x, y)$.
  2. Generación de máscara binaria con umbral de tolerancia $\theta = 15$:
     $$M(x, y) = \begin{cases} 1 & \text{si } I_{gray}(x, y) > 15 \\ 0 & \text{en otro caso} \end{cases}$$
  3. Cálculo de la caja delimitadora (*Bounding Box*) que encierra las coordenadas activas $[(x_{min}, y_{min}), (x_{max}, y_{max})]$.
  4. Aplicación de padding simétrico para asegurar que la imagen recortada sea exactamente cuadrada ($h = w$) sin alterar la relación de aspecto anatómica del globo ocular.

### 3.2 Ecualización Adaptativa de Histograma Limitada por Contraste (CLAHE)
La ecualización de histograma tradicional amplifica el ruido de fondo en regiones homogéneas. CLAHE resuelve esto dividiendo la imagen en bloques locales contextuales (*tiles*) y limitando la pendiente de la función acumulativa de distribución (CDF).
* **Espacio de Color:** Se transforma la imagen al espacio perceptualmente uniforme **CIE LAB**, aplicando el algoritmo exclusivamente sobre el canal de luminosidad ($L^*$), preservando los componentes cromáticos $a^*$ y $b^*$.
* **Parámetros Clínicos Calibrados:**
  * `clipLimit = 2.0`: Umbral de corte que redistribuye el exceso de contraste para evitar la creación de artefactos luminosos en la mácula.
  * `tileGridSize = (8, 8)`: Rejilla de $8 \times 8$ bloques locales con interpolación bilineal entre bordes de teselas, resaltando eficazmente los microvasos sanguíneos de la retina y la excavación de la copa óptica.

### 3.3 Redimensionamiento y Normalización
* **Resolución Objetivo:** $224 \times 224 \times 3$ píxeles, correspondiente a la topología de entrada estándar de **DenseNet121** preentrenada en ImageNet.
* **Interpolación:** `cv2.INTER_CUBIC` (interpolación bicúbica sobre vecindario de $4 \times 4$ píxeles), minimizando la pérdida de nitidez en microaneurismas y hemorragias punteadas.
* **Normalización:** División aritmética por $255.0$, transformando los valores enteros $[0, 255]$ a punto flotante continuo $[0.0, 1.0]$.

---

## 4. METODOLOGÍA DE DATA AUGMENTATION Y BALANCEO

El módulo implementado en [`scripts/augment.py`](file:///c:/Users/Lucero/Documents/TP1-RetiScan/scripts/augment.py) previene el sobreajuste (*overfitting*) y balancea las clases minoritarias aplicando transformaciones estocásticas que conservan el valor diagnóstico de la patología:

### 4.1 Principio de Prevención de Fuga de Datos (*Zero Data Leakage*)
> [!CAUTION]
> **Regla de Oro en Machine Learning Médico:** Las técnicas de aumento sintético de datos **nunca** deben aplicarse sobre los conjuntos de Validación (*Val*) ni de Prueba (*Test*). La partición estratificada se realiza **antes** de generar cualquier variación sintética, asegurando que las evaluaciones reflejen la capacidad de generalización del modelo ante imágenes no vistas.

### 4.2 Transformaciones Geométricas y Fotométricas Permitidas
1. **Rotación Aleatoria Controlada ($\pm 25^\circ$):** Simula ligeras variaciones angulares en la posición de la cabeza del paciente frente a la mentonera del retinógrafo, usando relleno reflectivo en bordes.
2. **Inversión Horizontal (*Horizontal Flip* - $p=0.5$):** Simula la simetría bilateral entre ojo derecho (OD) y ojo izquierdo (OS) sin alterar la presencia de exudados ni excavaciones.
3. **Inversión Vertical (*Vertical Flip* - $p=0.25$):** Aplicada con baja probabilidad para aumentar la invarianza espacial del extractor de características.
4. **Variación Sutil de Brillo y Contraste:** Factor de contraste $\alpha \in [0.90, 1.12]$ y sesgo de brillo $\beta \in [-12, 12]$, simulando variaciones en la potencia del flash del retinógrafo.
5. **Escalado / Zoom Sutil ($0.96 \times$ a $1.06 \times$):** Simula variaciones milimétricas en la distancia pupilar de enfoque.

---

## 5. ESTRUCTURA DEL REPOSITORIO Y MANIFIESTO FORMAL

El orquestador en [`scripts/build_dataset.py`](file:///c:/Users/Lucero/Documents/TP1-RetiScan/scripts/build_dataset.py) organiza los datos en la siguiente estructura física:

```text
TP1-RetiScan/
├── data/
│   ├── raw/                             # Imágenes crudas por clase
│   │   ├── healthy/
│   │   ├── diabetic_retinopathy/
│   │   └── glaucoma/
│   ├── processed/                       # Particiones optimizadas a 224x224
│   │   ├── train/                       # 70% + Variaciones sintéticas
│   │   │   ├── healthy/
│   │   │   ├── diabetic_retinopathy/
│   │   │   └── glaucoma/
│   │   ├── val/                         # 15% (Imágenes originales preprocesadas)
│   │   │   ├── healthy/
│   │   │   ├── diabetic_retinopathy/
│   │   │   └── glaucoma/
│   │   └── test/                        # 15% (Imágenes de prueba ciega)
│   │       ├── healthy/
│   │       ├── diabetic_retinopathy/
│   │       └── glaucoma/
│   └── dataset_manifest.csv             # Catálogo de metadatos e índices
```

### 5.1 Especificación del Archivo `dataset_manifest.csv`
Cada muestra procesada queda indexada formalmente con los siguientes campos:

| Campo | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `image_id` | String | Identificador alfanumérico único estandarizado | `RET_HEA_00001` / `RET_DIA_00007_AUG` |
| `class_name` | String | Nombre taxonómico de la clase médica | `healthy`, `diabetic_retinopathy`, `glaucoma` |
| `label_idx` | Integer | Índice numérico para la capa de salida Softmax | `0` (Sano), `1` (RD), `2` (Glaucoma) |
| `split` | String | Subconjunto experimental asignado | `train`, `val`, `test` |
| `is_augmented` | Boolean | Indicador de muestra sintética de balanceo | `False` (original), `True` (sintética) |
| `original_file` | String | Nombre del archivo fuente crudo | `sample_dr_01.png` |
| `relative_path` | String | Ruta de acceso relativo al tensor procesado | `processed\train\glaucoma\RET_GLA_00011_train.png` |
| `resolution` | String | Dimensiones espaciales estandarizadas | `224x224` |
| `channels` | Integer | Número de canales espectrales | `3` (RGB/BGR) |

---

## 6. PRUEBAS DE VERIFICACIÓN Y VALIDACIÓN TÉCNICA

Para garantizar la robustez del código, se desarrolló la suite de pruebas automatizadas en [`scripts/test_pipeline.py`](file:///c:/Users/Lucero/Documents/TP1-RetiScan/scripts/test_pipeline.py), evaluando cinco dimensiones operativas:

```
[TEST 1] test_crop_retina_roi .......... OK  (Verifica recorte cuadrático sin distorsión)
[TEST 2] test_apply_clahe .............. OK  (Verifica conservación de tipo uint8 y canales)
[TEST 3] test_resize_and_normalize ..... OK  (Verifica salida 224x224 y valores en [0.0, 1.0])
[TEST 4] test_data_augmentation ........ OK  (Verifica estabilidad de transformaciones estocásticas)
[TEST 5] test_end_to_end_pipeline ...... OK  (Verifica flujo completo y generación de manifest CSV)

----------------------------------------------------------------------
Ran 5 tests in 0.710s | RESULTADO: OK (100% pruebas superadas)
```

---

## 7. INSTRUCCIONES DE OPERACIÓN

Cuando se disponga de nuevos lotes de retinografías procedentes del **Centro Oftalmológico V.E.R.** o de datasets complementarios de Kaggle:

1. Colocar las imágenes crudas en sus respectivas carpetas:
   * `data/raw/healthy/`
   * `data/raw/diabetic_retinopathy/`
   * `data/raw/glaucoma/`
2. Ejecutar el compilador desde la terminal:
   ```powershell
   python scripts/build_dataset.py --train-target 500
   ```
3. El script limpiará, recortará la ROI, aplicará el filtro CLAHE, balanceará la partición `train` hasta 500 muestras por clase y actualizará `data/dataset_manifest.csv` en cuestión de minutos.

---

## 8. CONCLUSIÓN DEL ENTREGABLE OE1-I2
El repositorio de datos y el pipeline de ingeniería de imágenes quedan formalmente operativos, estandarizados y testeados. Con este componente finalizado, se cumple íntegramente con los requisitos del **Objetivo Específico 1 (OE1)**, dejando el terreno listo para proceder con el **Objetivo Específico 2 (OE2)**: el diseño y entrenamiento de la arquitectura **DenseNet121**.
