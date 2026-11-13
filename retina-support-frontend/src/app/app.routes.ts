import { Routes } from '@angular/router';

import { InstitutionalLogin } from './pages/auth/institutional-login/institutional-login';
import { AdminLogin } from './pages/auth/admin-login/admin-login';
import { AdminDashboard } from './pages/admin/admin-dashboard/admin-dashboard';
import { PatientCreate } from './pages/patients/patient-create/patient-create';
import { PatientList } from './pages/patients/patient-list/patient-list';
import { PatientDetail } from './pages/patients/patient-detail/patient-detail';
import { EvaluationCreate } from './pages/evaluations/evaluation-create/evaluation-create';
import { RetinographyUpload } from './pages/evaluations/retinography-upload/retinography-upload';


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
        component: AdminDashboard
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
        path: 'evaluations/:evaluationId/retinography',
        component: RetinographyUpload
    },
    {
        path: '**',
        redirectTo: 'login'
    }
];
