import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { InvoiceUploadComponent } from './components/invoice-upload/invoice-upload.component';
import { InvoiceDetailsComponent } from './components/invoice-details/invoice-details.component';

const routes: Routes = [
  { path: '', component: InvoiceUploadComponent },
  { path: 'invoices/:id', component: InvoiceDetailsComponent },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }