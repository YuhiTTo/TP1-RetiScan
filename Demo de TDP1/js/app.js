/**
 * APLICACIÓN WEB DE SOPORTE CLÍNICO - ENGINE JS
 * Detección de Patologías Retinianas mediante DenseNet121 + FastAPI
 * Centro Oftalmológico V.E.R. / INO - Lima Metropolitana
 */

document.addEventListener('DOMContentLoaded', () => {
  // Preset Data Configuration
  const PRESETS = {
    healthy: {
      title: 'Sin Hallazgos Patológicos (Normal)',
      sub: 'Estructura retiniana dentro de parámetros fisiológicos normales.',
      code: 'HEALTHY_01',
      img: 'assets/images/fundus_healthy.png',
      probabilities: {
        healthy: 98.4,
        diabetic: 1.2,
        glaucoma: 0.4
      },
      recommendations: 'No se observan microaneurismas ni excavación glaucomatosa. Se sugiere control rutinario preventivo en 12 meses.'
    },
    diabetic: {
      title: 'Retinopatía Diabética (Moderada / Severa)',
      sub: 'Detección de microaneurismas, exudados duros y microhemorragias vascularizadas.',
      code: 'DR_SEV_04',
      img: 'assets/images/fundus_diabetic_retinopathy.png',
      probabilities: {
        healthy: 2.1,
        diabetic: 95.8,
        glaucoma: 2.1
      },
      recommendations: 'Prioridad Alta: Se requiere derivación a especialista en Retina en < 7 días. Tratamiento láser / anti-VEGF evaluable.'
    },
    glaucoma: {
      title: 'Glaucoma (Sospecha / Excavación Aumentada)',
      sub: 'Relación copa-disco (CDR > 0.65) aumentada y adelgazamiento de capa de fibras nerviosas.',
      code: 'GLAUCOMA_02',
      img: 'assets/images/fundus_glaucoma.png',
      probabilities: {
        healthy: 1.5,
        diabetic: 3.2,
        glaucoma: 95.3
      },
      recommendations: 'Prioridad Urgente: Evaluación de Presión Intraocular (PIO) y campo visual en especialidad de Glaucoma en < 5 días.'
    }
  };

  let currentPresetKey = 'healthy';
  let isAnalyzing = false;
  let currentFilter = 'normal';

  // DOM Elements
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  const presetBtns = document.querySelectorAll('.preset-btn');
  const fundusViewport = document.getElementById('fundusViewport');
  const scanLine = document.getElementById('scanLine');
  const filterBtns = document.querySelectorAll('.filter-btn');
  const btnRunInference = document.getElementById('btnRunInference');

  // Results DOM
  const resultCard = document.getElementById('resultCard');
  const diagBanner = document.getElementById('diagBanner');
  const diagTitle = document.getElementById('diagTitle');
  const diagSubtitle = document.getElementById('diagSubtitle');
  const diagConfidence = document.getElementById('diagConfidence');

  const probHealthyBar = document.getElementById('probHealthyBar');
  const probHealthyVal = document.getElementById('probHealthyVal');
  const probDiabeticBar = document.getElementById('probDiabeticBar');
  const probDiabeticVal = document.getElementById('probDiabeticVal');
  const probGlaucomaBar = document.getElementById('probGlaucomaBar');
  const probGlaucomaVal = document.getElementById('probGlaucomaVal');
  const textRecommendations = document.getElementById('textRecommendations');

  // Patient Modal & Report DOM
  const btnOpenReport = document.getElementById('btnOpenReport');
  const reportModal = document.getElementById('reportModal');
  const btnCloseReport = document.getElementById('btnCloseReport');
  const btnPrintReport = document.getElementById('btnPrintReport');

  // Tab Navigation Logic
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
    });
  });

  // Preset Selector Logic
  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      presetBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPresetKey = btn.getAttribute('data-preset');
      loadPreset(currentPresetKey);
    });
  });

  function loadPreset(key) {
    const data = PRESETS[key];
    if (!data) return;
    fundusViewport.src = data.img;
    resetResultsView();
  }

  // Filter Buttons (Normal, CLAHE, Heatmap Grad-CAM)
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter');
      applyFilter(currentFilter);
    });
  });

  function applyFilter(filter) {
    if (filter === 'clahe') {
      fundusViewport.style.filter = 'contrast(160%) brightness(90%) hue-rotate(15deg)';
    } else if (filter === 'heatmap') {
      fundusViewport.style.filter = 'contrast(200%) saturate(300%) invert(30%) sepia(80%)';
    } else {
      fundusViewport.style.filter = 'none';
    }
  }

  // File Upload Handling
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--accent-cyan)';
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.style.borderColor = 'var(--border-accent)';
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--border-accent)';
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleUploadedFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleUploadedFile(e.target.files[0]);
      }
    });
  }

  function handleUploadedFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      fundusViewport.src = e.target.result;
      currentPresetKey = 'diabetic'; // Default simulation for uploaded image
      resetResultsView();
    };
    reader.readAsDataURL(file);
  }

  function resetResultsView() {
    probHealthyBar.style.width = '0%';
    probHealthyVal.textContent = '0%';
    probDiabeticBar.style.width = '0%';
    probDiabeticVal.textContent = '0%';
    probGlaucomaBar.style.width = '0%';
    probGlaucomaVal.textContent = '0%';
    diagBanner.className = 'diagnosis-banner hidden';
    btnOpenReport.classList.add('hidden');
  }

  // AI Inference Simulation (DenseNet121 + FastAPI)
  btnRunInference.addEventListener('click', () => {
    if (isAnalyzing) return;
    isAnalyzing = true;
    btnRunInference.disabled = true;
    btnRunInference.innerHTML = `<svg class="spin" style="width:20px;height:20px;animation:spin 1s linear infinite" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.3"></circle><path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Procesando con DenseNet121...`;
    
    scanLine.style.display = 'block';

    setTimeout(() => {
      scanLine.style.display = 'none';
      btnRunInference.disabled = false;
      btnRunInference.innerHTML = `<svg viewBox="0 0 24 24" style="width:20px;height:20px;fill:currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg> Ejecutar Inferencia de IA`;
      isAnalyzing = false;
      
      displayAIResults(currentPresetKey);
    }, 1400);
  });

  function displayAIResults(key) {
    const data = PRESETS[key] || PRESETS.healthy;
    
    // Update Banner
    diagBanner.classList.remove('hidden', 'healthy', 'diabetic', 'glaucoma');
    diagBanner.classList.add(key);
    diagTitle.textContent = data.title;
    diagSubtitle.textContent = data.sub;

    const topProb = Math.max(data.probabilities.healthy, data.probabilities.diabetic, data.probabilities.glaucoma);
    diagConfidence.textContent = `${topProb.toFixed(1)}% Confianza`;

    // Update Progress Bars
    probHealthyBar.style.width = `${data.probabilities.healthy}%`;
    probHealthyVal.textContent = `${data.probabilities.healthy}%`;

    probDiabeticBar.style.width = `${data.probabilities.diabetic}%`;
    probDiabeticVal.textContent = `${data.probabilities.diabetic}%`;

    probGlaucomaBar.style.width = `${data.probabilities.glaucoma}%`;
    probGlaucomaVal.textContent = `${data.probabilities.glaucoma}%`;

    textRecommendations.textContent = data.recommendations;
    btnOpenReport.classList.remove('hidden');

    // Smooth Scroll to Results
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Report Modal Open/Close
  btnOpenReport.addEventListener('click', () => {
    fillReportModalData();
    reportModal.classList.add('active');
  });

  btnCloseReport.addEventListener('click', () => {
    reportModal.classList.remove('active');
  });

  btnPrintReport.addEventListener('click', () => {
    window.print();
  });

  function fillReportModalData() {
    const data = PRESETS[currentPresetKey];
    document.getElementById('rptDate').textContent = new Date().toLocaleDateString('es-PE', { year: 'numeric', month: 'long', day: 'numeric' });
    document.getElementById('rptDiagnosisTitle').textContent = data.title;
    document.getElementById('rptConfidence').textContent = `${Math.max(data.probabilities.healthy, data.probabilities.diabetic, data.probabilities.glaucoma)}%`;
    document.getElementById('rptRecommendations').textContent = data.recommendations;
    document.getElementById('rptFundusImg').src = data.img;
  }
});
