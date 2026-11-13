import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AdminEstablishmentService, Establishment, EstablishmentDetail, CreateInstitutionalAccountRequest, UpdateEstablishmentRequest } from '../../../core/services/admin-establishment';

@Component({
  selector: 'app-admin-dashboard',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.css'
})
export class AdminDashboard implements OnInit {


  establishments: Establishment[] = [];

  loading = false;

  errorMessage = '';

  showCreateModal = false;
  showEditModal = false;

  selectedEstablishment: Establishment | null = null;

  editLoading = false;
  editErrorMessage = '';

  editEstablishmentName = '';
  editEstablishmentRuc = '';
  editEstablishmentAddress = '';
  editEstablishmentDistrict = '';
  editEstablishmentPhone = '';
  editEstablishmentStatus = true;

  editInstitutionalEmail = '';
  editNewPassword = '';

  creating = false;
  createErrorMessage = '';

  establishmentName = '';
  establishmentRuc = '';
  establishmentAddress = '';
  establishmentDistrict = '';
  establishmentPhone = '';
  establishmentStatus = true;

  institutionalEmail = '';
  initialPassword = '';
  searchTerm = '';
  statusFilter = '';
  currentPage = 1;
  itemsPerPage = 5;

  savingEdit = false;

  showCredentialsModal = false;

  credentialsLoading = false;
  credentialsErrorMessage = '';

  credentialsCode = '';
  credentialsEmail = '';
  credentialsStatus = true;
  credentialsName = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Administrador';


  constructor(
    private router: Router,
    private adminEstablishmentService: AdminEstablishmentService,
    private cdr: ChangeDetectorRef,
  ) {
  }


  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/admin/login']);
  }

  ngOnInit(): void {
    this.loadEstablishments();
  }

  loadEstablishments(): void {

    this.loading = true;
    this.errorMessage = '';

    this.adminEstablishmentService
      .getEstablishments()
      .subscribe({

        next: (response) => {

          this.establishments = response;
          this.loading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.loading = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 403) {

            this.errorMessage =
              'No tiene permisos para acceder a los establecimientos.';

          } else {

            this.errorMessage =
              'No se pudieron cargar los establecimientos.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  get filteredEstablishments(): Establishment[] {

    const search =
      this.searchTerm.trim().toLowerCase();

    return this.establishments.filter(
      (establishment) => {

        const matchesSearch =
          !search ||
          establishment.nombre
            .toLowerCase()
            .includes(search) ||

          (establishment.ruc ?? '')
            .toLowerCase()
            .includes(search) ||

          establishment.distrito
            .toLowerCase()
            .includes(search);


        const matchesStatus =
          !this.statusFilter ||

          (
            this.statusFilter === 'active'
            && establishment.estado
          ) ||

          (
            this.statusFilter === 'inactive'
            && !establishment.estado
          );


        return matchesSearch && matchesStatus;
      }
    );
  }

  get totalPages(): number {

    return Math.max(
      1,
      Math.ceil(
        this.filteredEstablishments.length
        / this.itemsPerPage
      )
    );
  }


  get paginatedEstablishments(): Establishment[] {

    const start =
      (this.currentPage - 1)
      * this.itemsPerPage;

    const end =
      start + this.itemsPerPage;

    return this.filteredEstablishments.slice(
      start,
      end
    );
  }


  previousPage(): void {

    if (this.currentPage > 1) {
      this.currentPage--;
    }
  }


  nextPage(): void {

    if (this.currentPage < this.totalPages) {
      this.currentPage++;
    }
  }


  goToPage(page: number): void {

    if (
      page >= 1 &&
      page <= this.totalPages
    ) {
      this.currentPage = page;
    }
  }

  openCreateModal(): void {

    this.createErrorMessage = '';

    this.showCreateModal = true;
  }

  openEditModal(
    establishment: Establishment
  ): void {

    this.selectedEstablishment = establishment;

    this.editLoading = true;
    this.editErrorMessage = '';

    this.showEditModal = true;

    this.adminEstablishmentService
      .getEstablishmentDetail(
        establishment.id_establecimiento
      )
      .subscribe({

        next: (response: EstablishmentDetail) => {

          this.editEstablishmentName =
            response.nombre;

          this.editEstablishmentRuc =
            response.ruc ?? '';

          this.editEstablishmentAddress =
            response.direccion;

          this.editEstablishmentDistrict =
            response.distrito;

          this.editEstablishmentPhone =
            response.telefono;

          this.editEstablishmentStatus =
            response.estado;

          this.editInstitutionalEmail =
            response.correo_electronico;

          // Siempre vacío porque nunca mostramos
          // la contraseña actual.
          this.editNewPassword = '';

          this.editLoading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.editLoading = false;

          if (error.status === 401) {

            this.logout();

            return;
          }

          if (error.status === 404) {

            this.editErrorMessage =
              'No se encontró el establecimiento.';

          } else {

            this.editErrorMessage =
              'No se pudieron cargar los datos del establecimiento.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  openCredentialsModal(
    establishment: Establishment
  ): void {

    this.credentialsLoading = true;
    this.credentialsErrorMessage = '';

    this.showCredentialsModal = true;

    this.adminEstablishmentService
      .getEstablishmentDetail(
        establishment.id_establecimiento
      )
      .subscribe({

        next: (response: EstablishmentDetail) => {

          this.credentialsCode =
            response.codigo_institucional;

          this.credentialsEmail =
            response.correo_electronico;

          this.credentialsStatus =
            response.estado;

          this.credentialsName =
            response.nombre;

          this.credentialsLoading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.credentialsLoading = false;

          if (error.status === 401) {

            this.logout();
            return;

          } else if (error.status === 404) {

            this.credentialsErrorMessage =
              'No se encontró la información del establecimiento.';

          } else {

            this.credentialsErrorMessage =
              'No se pudieron cargar las credenciales.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  closeEditModal(): void {

    if (this.editLoading) {
      return;
    }

    this.showEditModal = false;

    this.selectedEstablishment = null;

    this.editErrorMessage = '';
    this.editNewPassword = '';
  }

  closeCredentialsModal(): void {

    this.showCredentialsModal = false;

    this.credentialsCode = '';
    this.credentialsEmail = '';
    this.credentialsName = '';
    this.credentialsErrorMessage = '';
  }

  saveEditEstablishment(): void {

    if (!this.selectedEstablishment) {
      return;
    }

    if (
      !this.editEstablishmentName.trim() ||
      !this.editEstablishmentAddress.trim() ||
      !this.editEstablishmentDistrict.trim() ||
      !this.editEstablishmentPhone.trim() ||
      !this.editInstitutionalEmail.trim()
    ) {
      this.editErrorMessage =
        'Complete todos los campos obligatorios.';

      return;
    }

    const data: UpdateEstablishmentRequest = {

      nombre:
        this.editEstablishmentName.trim(),

      ruc:
        this.editEstablishmentRuc.trim() || null,

      direccion:
        this.editEstablishmentAddress.trim(),

      distrito:
        this.editEstablishmentDistrict.trim(),

      telefono:
        this.editEstablishmentPhone.trim(),

      estado:
        this.editEstablishmentStatus,

      correo_electronico:
        this.editInstitutionalEmail.trim(),

      nueva_password:
        this.editNewPassword.trim() || null
    };


    this.savingEdit = true;
    this.editErrorMessage = '';


    this.adminEstablishmentService
      .updateEstablishment(
        this.selectedEstablishment.id_establecimiento,
        data
      )
      .subscribe({

        next: () => {

          this.savingEdit = false;

          this.showEditModal = false;

          this.selectedEstablishment = null;

          this.editNewPassword = '';

          // Actualiza la tabla.
          this.loadEstablishments();

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.savingEdit = false;

          if (error.status === 401) {

            this.logout();
            return;

          } else if (error.status === 403) {

            this.editErrorMessage =
              'No tiene permisos para editar establecimientos.';

          } else if (error.status === 404) {

            this.editErrorMessage =
              'No se encontró el establecimiento.';

          } else if (error.status === 409) {

            this.editErrorMessage =
              'El correo institucional ya está registrado en otra cuenta.';

          } else if (error.status === 422) {

            this.editErrorMessage =
              'Verifique los datos ingresados.';

          } else {

            this.editErrorMessage =
              'No se pudieron guardar los cambios.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  closeCreateModal(): void {

    if (this.creating) {
      return;
    }

    this.showCreateModal = false;

    this.resetCreateForm();
  }


  resetCreateForm(): void {

    this.establishmentName = '';
    this.establishmentRuc = '';
    this.establishmentAddress = '';
    this.establishmentDistrict = '';
    this.establishmentPhone = '';
    this.establishmentStatus = true;

    this.institutionalEmail = '';
    this.initialPassword = '';

    this.createErrorMessage = '';
  }


  createEstablishment(): void {

    if (
      !this.establishmentName.trim() ||
      !this.establishmentAddress.trim() ||
      !this.establishmentDistrict.trim() ||
      !this.establishmentPhone.trim() ||
      !this.institutionalEmail.trim() ||
      !this.initialPassword
    ) {
      this.createErrorMessage =
        'Complete todos los campos obligatorios.';

      return;
    }


    const data: CreateInstitutionalAccountRequest = {

      establecimiento: {

        nombre:
          this.establishmentName.trim(),

        ruc:
          this.establishmentRuc.trim() || null,

        direccion:
          this.establishmentAddress.trim(),

        distrito:
          this.establishmentDistrict.trim(),

        telefono:
          this.establishmentPhone.trim(),

        estado:
          this.establishmentStatus
      },

      cuenta: {

        correo_electronico:
          this.institutionalEmail.trim(),

        password:
          this.initialPassword,

        nombre_mostrado:
          this.establishmentName.trim()
      }
    };


    this.creating = true;
    this.createErrorMessage = '';


    this.adminEstablishmentService
      .createEstablishment(data)
      .subscribe({

        next: () => {

          this.creating = false;

          this.showCreateModal = false;

          this.resetCreateForm();

          // Recarga la tabla automáticamente.
          this.loadEstablishments();

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.creating = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 403) {

            this.createErrorMessage =
              'No tiene permisos para registrar establecimientos.';

          } else if (error.status === 409) {

            this.createErrorMessage =
              'El correo institucional ya se encuentra registrado.';

          } else if (error.status === 422) {

            this.createErrorMessage =
              'Verifique los datos ingresados.';

          } else {

            this.createErrorMessage =
              'No se pudo registrar el establecimiento.';
          }

          this.cdr.markForCheck();
        }
      });
  }
}