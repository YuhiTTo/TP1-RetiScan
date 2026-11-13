# US-12 - Validación de calidad mínima de retinografías

Este directorio contiene los experimentos realizados para definir, validar y auditar los criterios técnicos de calidad de imagen correspondientes a la historia de usuario US-12 de RetiScan.

## Objetivo

Determinar criterios reproducibles para clasificar una retinografía como:

- SUFICIENTE
- INSUFICIENTE

antes de ejecutar el preprocesamiento de inferencia y los modelos de Retinopatía Diabética y Glaucoma.

## Flujo implementado

Retinografía
→ validación de archivo e integridad (US-11)
→ validación de calidad mínima (US-12)
→ preprocesamiento para inferencia (US-13)
→ modelos RD y Glaucoma (US-14/US-15)

La validación de calidad no modifica la imagen original ni altera el preprocesamiento o los modelos CNN existentes.

## Regla final de calidad

Una imagen se considera SUFICIENTE cuando cumple simultáneamente:

clarity_gradient_p90 >= 16.06225775

dark_ratio_30 <= 0.33113740

contrast_cv <= 0.63830344

y el FOV retinal puede detectarse técnicamente.

## FOV

Inicialmente se probaron límites geométricos derivados de DeepDRiD.

Sin embargo:

- Chākṣu rechazaba 1345/1345 imágenes (100 %).
- APTOS rechazaba 3968/5590 imágenes (70.98 %).

Por ello, esos límites geométricos fueron descartados como criterio de producción.

Actualmente el FOV solo comprueba que:

- exista una región retinal detectable;
- exista un contorno válido;
- la región tenga dimensiones válidas;
- la ROI pueda normalizarse;
- la máscara retinal no quede vacía.

Si el archivo puede leerse pero no se detecta una región retinal utilizable, la imagen se clasifica como INSUFICIENTE.

## Datasets utilizados

### DeepDRiD

- Set-A: 1200 imágenes.
- Set-B: 400 imágenes.

Se utilizó para desarrollo de métricas, derivación de thresholds y validación sin reajuste.

### MSHF

Se utilizaron 499 imágenes CFP para estudiar la robustez de las métricas de claridad, iluminación y contraste.

### Chākṣu

Se auditaron 1345 imágenes originales.

Resultado:

- SUFICIENTE: 1066/1345 (79.26 %).
- INSUFICIENTE: 279/1345 (20.74 %).
- Errores: 0.

### APTOS 2019

Se auditaron 5590 imágenes originales.

Resultado:

- SUFICIENTE: 4181/5590 (74.79 %).
- INSUFICIENTE: 1409/5590 (25.21 %).
- Errores: 0.

Chākṣu y APTOS se utilizaron como auditorías de transferencia. No se reajustaron los thresholds con estos datasets.

## Validación de integración

Se comprobaron los siguientes escenarios:

### Imagen suficiente

P10_Image2.JPG

Resultado:

- calidad = SUFICIENTE;
- se creó ANALISIS_IA;
- se crearon las ejecuciones RD y Glaucoma;
- el flujo continuó normalmente.

### Imagen insuficiente

000c1434d8d7.png

Resultado:

- fallo por claridad;
- calidad = INSUFICIENTE;
- HTTP 422;
- no se creó ANALISIS_IA;
- no se creó ninguna EJECUCION_MODELO.

### Reemplazo

Al reemplazar una imagen insuficiente:

- calidad_imagen volvió a NULL;
- la nueva imagen fue evaluada nuevamente;
- si fue SUFICIENTE, el análisis continuó normalmente.

### FOV no detectable

Una imagen válida y decodificable sin región retinal fue clasificada como:

- INSUFICIENTE;
- failed_criteria = ["fov"].

## Estructura

- scripts/: scripts experimentales.
- results/: resultados CSV y TXT.
- figures/: evidencias visuales.

Los datasets originales no se almacenan en Git.

## Reproducibilidad

Los thresholds geométricos descartados de FOV se conservan únicamente para reproducir los experimentos que justificaron su exclusión.

No participan en la decisión final de producción.
