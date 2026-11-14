import { ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { EvaluationDetail, EvaluationService } from '../../../core/services/evaluation';


@Component({
  selector: 'app-retinography-upload',
  imports: [
    CommonModule
  ],
  templateUrl: './retinography-upload.html',
  styleUrl: './retinography-upload.css'
})
export class RetinographyUpload implements OnInit {

  evaluationId = 0;
  evaluation: EvaluationDetail | null = null;

  loading = true;
  errorMessage = '';
  displayName = localStorage.getItem('display_name') ?? 'Establecimiento';
  selectedFile: File | null = null;
  previewUrl: string | null = null;

  fileName = '';
  fileSize = '';
  fileFormat = '';

  fileErrorMessage = '';

  isUploading = false;

  uploadSuccessMessage = '';

  retinographyUploaded = false;

  isAnalyzing = false;

  analysisErrorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private evaluationService: EvaluationService,
    private cdr: ChangeDetectorRef
  ) {
  }


  ngOnInit(): void {

    this.evaluationId = Number(
      this.route.snapshot.paramMap.get(
        'evaluationId'
      )
    );

    if (!this.evaluationId) {

      this.errorMessage =
        'Identificador de evaluación no válido.';

      this.loading = false;

      return;
    }

    this.loadEvaluation();
  }

  loadEvaluation(): void {

    this.loading = true;
    this.errorMessage = '';

    this.evaluationService
      .getEvaluationDetail(
        this.evaluationId
      )
      .subscribe({

        next: (response) => {

          this.evaluation = response;

          this.loading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.loading = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 404) {

            this.errorMessage =
              'La evaluación no fue encontrada.';

          } else {

            this.errorMessage =
              'No se pudo cargar la información de la evaluación.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  calculateAge(birthDate: string): number {

    const birth = new Date(birthDate);
    const today = new Date();

    let age =
      today.getFullYear()
      - birth.getFullYear();

    const monthDifference =
      today.getMonth()
      - birth.getMonth();

    if (
      monthDifference < 0 ||
      (
        monthDifference === 0 &&
        today.getDate() < birth.getDate()
      )
    ) {
      age--;
    }

    return age;
  }

  goBack(): void {

    if (!this.evaluation) {
      return;
    }

    this.router.navigate([
      '/patients',
      this.evaluation.id_paciente
    ]);
  }


  onFileSelected(event: Event): void {

    const input = event.target as HTMLInputElement;

    if (!input.files || input.files.length === 0) {
      return;
    }

    const file = input.files[0];

    this.fileErrorMessage = '';
    this.uploadSuccessMessage = '';

    // Evitamos conservar un archivo pendiente anterior.
    this.selectedFile = null;

    // 1. Validar formato
    const allowedTypes = [
      'image/jpeg',
      'image/png'
    ];

    if (!allowedTypes.includes(file.type)) {

      this.fileErrorMessage =
        'Seleccione una imagen JPG, JPEG o PNG.';

      input.value = '';
      this.cdr.markForCheck();
      return;
    }

    // 2. Validar que el archivo no esté vacío
    if (file.size === 0) {

      this.fileErrorMessage =
        'El archivo está vacío o dañado. Seleccione otra imagen.';

      input.value = '';
      this.cdr.markForCheck();
      return;
    }

    // 3. Validar tamaño máximo
    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {

      this.fileErrorMessage =
        'La imagen no puede superar los 10 MB.';

      input.value = '';
      this.cdr.markForCheck();
      return;
    }

    // 4. Comprobar que el contenido sea una imagen legible
    const objectUrl = URL.createObjectURL(file);

    const image = new Image();

    image.onload = () => {

      if (
        image.naturalWidth <= 0 ||
        image.naturalHeight <= 0
      ) {

        URL.revokeObjectURL(objectUrl);

        this.fileErrorMessage =
          'El archivo no es una imagen válida o está dañado. Seleccione otra imagen.';

        input.value = '';
        this.cdr.markForCheck();
        return;
      }

      // Liberar previsualización anterior
      if (this.previewUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(this.previewUrl);
      }

      // 5. Aceptar el archivo únicamente si es legible
      this.selectedFile = file;

      this.fileName = file.name;

      this.fileSize =
        (file.size / (1024 * 1024)).toFixed(2) + ' MB';

      this.fileFormat =
        file.name.split('.').pop()?.toUpperCase() ?? '';

      this.previewUrl = objectUrl;

      this.retinographyUploaded = false;

      this.cdr.markForCheck();
    };

    // Si el navegador no puede interpretar la imagen
    image.onerror = () => {

      URL.revokeObjectURL(objectUrl);

      this.fileErrorMessage =
        'El archivo no es una imagen válida o está dañado. Seleccione otra imagen.';

      input.value = '';

      this.cdr.markForCheck();
    };

    image.src = objectUrl;
  }

  uploadRetinography(): void {

    if (!this.selectedFile || this.isUploading) {
      return;
    }

    this.isUploading = true;
    this.fileErrorMessage = '';
    this.uploadSuccessMessage = '';

    this.evaluationService
      .uploadRetinography(
        this.evaluationId,
        this.selectedFile
      )
      .subscribe({

        next: () => {

          this.isUploading = false;

          this.retinographyUploaded = true;

          // Conservamos la previsualización,
          // pero liberamos el archivo pendiente de envío.
          this.selectedFile = null;

          this.uploadSuccessMessage =
            '¡Retinografía cargada y validada correctamente!';

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.isUploading = false;

          if (error.status === 401) {
            this.logout();
            return;
          }

          const backendMessage = error?.error?.detail;

          if (typeof backendMessage === 'string') {

            this.fileErrorMessage = backendMessage;

          } else if (error.status === 404) {

            this.fileErrorMessage =
              'La evaluación no fue encontrada.';

          } else {

            this.fileErrorMessage =
              'No se pudo cargar la retinografía. Inténtalo nuevamente.';
          }

          this.cdr.markForCheck();
        }

      });
  }

  analyzeRetinography(): void {

    if (
      !this.retinographyUploaded ||
      this.isAnalyzing ||
      this.isUploading
    ) {
      return;
    }

    this.isAnalyzing = true;
    this.analysisErrorMessage = '';

    this.evaluationService
      .analyzeEvaluation(this.evaluationId)
      .subscribe({

        next: (response) => {

          this.isAnalyzing = false;

          if (
            response.estado === 'COMPLETADO' ||
            response.estado === 'PARCIAL'
          ) {

            // La pantalla de resultados se conectará
            // en el siguiente paso.
            console.log(
              'Análisis recibido:',
              response
            );

          } else {

            this.analysisErrorMessage =
              'No se pudo completar el análisis. Puedes intentar nuevamente o reemplazar la retinografía.';
          }

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.isAnalyzing = false;

          if (error.status === 401) {
            this.logout();
            return;
          }

          this.analysisErrorMessage =
            typeof error?.error?.detail === 'string'
              ? error.error.detail
              : 'Ocurrió un error durante el análisis. Puedes intentar nuevamente o reemplazar la retinografía.';

          this.cdr.markForCheck();
        }
      });
  }

  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
