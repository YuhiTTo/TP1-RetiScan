import { Routes } from '@angular/router';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
    },
    {
        path: 'login',
        loadComponent: () =>
            import('./pages/auth/institutional-login/institutional-login')
                .then(m => m.InstitutionalLogin)
    },
    {
        path: 'admin/login',
        loadComponent: () =>
            import('./pages/auth/admin-login/admin-login')
                .then(m => m.AdminLogin)
    },
    {
        path: 'admin',
        redirectTo: 'admin/home',
        pathMatch: 'full'
    },
    {
        path: 'admin/home',
        canActivate: [adminGuard],
        loadComponent: () =>
            import('./pages/admin/admin-home/admin-home')
                .then(m => m.AdminHome)
    },
    {
        path: 'admin/establishments',
        canActivate: [adminGuard],
        loadComponent: () =>
            import('./pages/admin/admin-dashboard/admin-dashboard')
                .then(m => m.AdminDashboard)
    },
    {
        path: 'admin/evaluations',
        canActivate: [adminGuard],
        loadComponent: () =>
            import('./pages/admin/admin-evaluations/admin-evaluations')
                .then(m => m.AdminEvaluations)
    },
    {
        path: 'admin/consistency',
        canActivate: [adminGuard],
        loadComponent: () =>
            import('./pages/admin/admin-consistency/admin-consistency')
                .then(m => m.AdminConsistency)
    },
    {
        path: 'home',
        loadComponent: () =>
            import('./pages/home/home/home')
                .then(m => m.Home)
    },
    {
        path: 'patients',
        loadComponent: () =>
            import('./pages/patients/patient-list/patient-list')
                .then(m => m.PatientList)
    },
    {
        path: 'patients/new',
        loadComponent: () =>
            import('./pages/patients/patient-create/patient-create')
                .then(m => m.PatientCreate)
    },
    {
        path: 'patients/:id',
        loadComponent: () =>
            import('./pages/patients/patient-detail/patient-detail')
                .then(m => m.PatientDetail)
    },
    {
        path: 'patients/:id/evaluations/new',
        loadComponent: () =>
            import('./pages/evaluations/evaluation-create/evaluation-create')
                .then(m => m.EvaluationCreate)
    },
    {
        path: 'patients/:id/evaluations/:evaluationId/edit',
        loadComponent: () =>
            import('./pages/evaluations/evaluation-create/evaluation-create')
                .then(m => m.EvaluationCreate)
    },
    {
        path: 'evaluations',
        loadComponent: () =>
            import('./pages/evaluations/evaluation-list/evaluation-list')
                .then(m => m.EvaluationList)
    },
    {
        path: 'evaluations/:evaluationId/retinography',
        loadComponent: () =>
            import('./pages/evaluations/retinography-upload/retinography-upload')
                .then(m => m.RetinographyUpload)
    },
    {
        path: 'evaluations/:evaluationId/detail',
        loadComponent: () =>
            import('./pages/evaluations/evaluation-detail/evaluation-detail')
                .then(m => m.EvaluationDetail)
    },
    {
        path: 'evaluations/:evaluationId/results',
        loadComponent: () =>
            import('./pages/evaluations/evaluation-results/evaluation-results')
                .then(m => m.EvaluationResults)
    },
    {
        path: 'reports',
        loadComponent: () =>
            import('./pages/reports/report-list/report-list')
                .then(m => m.ReportList)
    },
    {
        path: '**',
        redirectTo: 'login'
    }
];