import { Routes } from '@angular/router';
import { adminGuard } from './core/guards/admin.guard';

import { InstitutionalLogin } from './pages/auth/institutional-login/institutional-login';
import { AdminLogin } from './pages/auth/admin-login/admin-login';
import { AdminDashboard } from './pages/admin/admin-dashboard/admin-dashboard';
import { AdminHome } from './pages/admin/admin-home/admin-home';
import { AdminEvaluations } from './pages/admin/admin-evaluations/admin-evaluations';
import { AdminConsistency } from './pages/admin/admin-consistency/admin-consistency';
import { Home } from './pages/home/home/home';
import { PatientCreate } from './pages/patients/patient-create/patient-create';
import { PatientList } from './pages/patients/patient-list/patient-list';
import { PatientDetail } from './pages/patients/patient-detail/patient-detail';
import { EvaluationCreate } from './pages/evaluations/evaluation-create/evaluation-create';
import { RetinographyUpload } from './pages/evaluations/retinography-upload/retinography-upload';
import { EvaluationList } from './pages/evaluations/evaluation-list/evaluation-list';
import { EvaluationResults } from './pages/evaluations/evaluation-results/evaluation-results';
import { EvaluationDetail } from './pages/evaluations/evaluation-detail/evaluation-detail';
import { ReportList } from './pages/reports/report-list/report-list';


export const routes: Routes = [
    {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
    },
    {
        path: 'login',
        component: InstitutionalLogin
    },
    {
        path: 'admin/login',
        component: AdminLogin
    },
    {
        path: 'admin',
        redirectTo: 'admin/home',
        pathMatch: 'full'
    },
    {
        path: 'admin/home',
        canActivate: [adminGuard],
        component: AdminHome
    },
    {
        path: 'admin/establishments',
        canActivate: [adminGuard],
        component: AdminDashboard
    },
    {
        path: 'admin/evaluations',
        canActivate: [adminGuard],
        component: AdminEvaluations
    },
    {
        path: 'admin/consistency',
        canActivate: [adminGuard],
        component: AdminConsistency
    },
    {
        path: 'home',
        component: Home
    },
    {
        path: 'patients',
        component: PatientList
    },
    {
        path: 'patients/new',
        component: PatientCreate
    },
    {
        path: 'patients/:id',
        component: PatientDetail
    },
    {
        path: 'patients/:id/evaluations/new',
        component: EvaluationCreate
    },
    {
        path: 'patients/:id/evaluations/:evaluationId/edit',
        component: EvaluationCreate
    },
    {
        path: 'evaluations',
        component: EvaluationList
    },
    {
        path: 'evaluations/:evaluationId/retinography',
        component: RetinographyUpload
    },
    {
        path: 'evaluations/:evaluationId/detail',
        component: EvaluationDetail
    },
    {
        path: 'evaluations/:evaluationId/results',
        component: EvaluationResults
    },
    {
        path: 'reports',
        component: ReportList
    },
    {
        path: '**',
        redirectTo: 'login'
    }
];
