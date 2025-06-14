import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Components
import { InvoiceUploadComponent } from './components/invoice-upload/invoice-upload.component';
import { InvoiceListComponent } from './components/invoice-list/invoice-list.component';
import { InvoiceDetailComponent } from './components/invoice-detail/invoice-detail.component';

// Services
import { ApiService } from './services/api.service';
import { AuthService } from './services/auth.service';

@NgModule({
  declarations: [
    AppComponent,
    InvoiceUploadComponent,
    InvoiceListComponent,
    InvoiceDetailComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule
  ],
  providers: [
    ApiService,
    AuthService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }