import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { InvoiceUploadComponent } from './components/invoice-upload/invoice-upload.component';
import { InvoiceListComponent } from './components/invoice-list/invoice-list.component';
import { InvoiceDetailComponent } from './components/invoice-detail/invoice-detail.component';

const routes: Routes = [
  { path: '', redirectTo: '/invoices', pathMatch: 'full' },
  { path: 'invoices', component: InvoiceListComponent },
  { path: 'invoices/:id', component: InvoiceDetailComponent },
  { path: 'upload', component: InvoiceUploadComponent },
  { path: '**', redirectTo: '/invoices' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }