import { Component } from '@angular/core';
import {
  ActivatedRoute,
  Router,
  RouterLink,
  RouterLinkActive
} from '@angular/router';

type AdminSection = 'home' | 'evaluations' | 'consistency';

@Component({
  selector: 'app-admin-section-preview',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <div class="page-container">

      <aside class="sidebar">

        <div class="sidebar-logo">
          <img src="/icons/retiscan2.png" alt="RetiScan">
        </div>

        <nav class="sidebar-menu" aria-label="Navegacion administrativa">

            <a class="menu-item"
                routerLink="/admin/home"
                routerLinkActive="active">
                <img src="/icons/home.png"
                    class="menu-icon-image" alt="">
                <span>Inicio</span>
            </a>

            <a class="menu-item"
                routerLink="/admin/establishments"
                routerLinkActive="active">
                <img src="/icons/hospital.png"
                    class="menu-icon-image" alt="">
                <span>Establecimientos</span>
            </a>

            <a class="menu-item"
                routerLink="/admin/evaluations"
                routerLinkActive="active">
                <img src="/icons/evaluation.png"
                    class="menu-icon-image" alt="">
                <span>Supervisión de evaluaciones</span>
            </a>

            <a class="menu-item"
                routerLink="/admin/consistency"
                routerLinkActive="active">
                <img src="/icons/reporte.png"
                    class="menu-icon-image" alt="">
                <span>Consistencia de registros</span>
            </a>

        </nav>

        <button type="button"
          class="logout-button"
          (click)="logout()">
          <img src="/icons/logout.png"
            class="menu-icon-image" alt="">
          <span>Cerrar sesión</span>
        </button>

      </aside>

      <main class="main-content">

        <header class="top-header">
          <div class="admin-card">
            <div class="admin-avatar">
              <img src="/icons/admin.png" alt="">
            </div>
            <div>
              <strong>{{ displayName }}</strong>
              <span>Administrador</span>
            </div>
          </div>
        </header>

        <section class="admin-preview">
          <h1>{{ title }}</h1>
          <p>{{ description }}</p>

          <p class="preview-note">
            Esta sección está en preparación.
            Todavía no presenta información operativa.
          </p>
        </section>

      </main>
    </div>
  `,
  styleUrls: [
    '../admin-dashboard/admin-dashboard.css'
  ],
  styles: [`
    .admin-preview {
      min-height: 360px;
      padding: 30px;
      background: white;
      border: 1px solid #cbd3dd;
      border-radius: 8px;
    }

    .admin-preview h1 {
      margin: 0 0 14px;
      font-size: 28px;
      color: #172033;
    }

    .admin-preview p {
      color: #596474;
      font-size: 14px;
      line-height: 1.6;
    }

    .admin-preview .preview-note {
      margin-top: 24px;
      color: #246dcc;
    }
  `]
})
export class AdminSectionPreview {

  readonly displayName =
    localStorage.getItem('display_name') ?? 'Administrador';

  readonly section: AdminSection;
  readonly title: string;
  readonly description: string;

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) {
    const value = this.route.snapshot.data['section'];

    this.section =
      value === 'evaluations' || value === 'consistency'
        ? value
        : 'home';

    const pages = {
      home: {
        title: 'Inicio administrativo',
        description:
          'Resumen general de la actividad de RetiScan.'
      },
      evaluations: {
        title: 'Supervisión de evaluaciones',
        description:
          'US-21: consulta de evaluaciones registradas, '
          + 'filtros y resumen por establecimiento.'
      },
      consistency: {
        title: 'Consistencia de registros',
        description:
          'US-22: revisión de asociaciones y '
          + 'detección de inconsistencias.'
      }
    };

    this.title = pages[this.section].title;
    this.description = pages[this.section].description;
  }

  logout(): void {
    for (const key of [
      'access_token',
      'account_type',
      'establishment_id',
      'display_name'
    ]) {
      localStorage.removeItem(key);
    }

    this.router.navigate(['/admin/login']);
  }
}
