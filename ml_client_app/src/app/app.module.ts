import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { InvoiceUploadComponent } from './components/invoice-upload/invoice-upload.component';
import { InvoiceDetailsComponent } from './components/invoice-details/invoice-details.component';

// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';

// Autres modules
import { NgxFileDropModule } from 'ngx-file-drop';

@NgModule({
  declarations: [
    AppComponent,
    InvoiceUploadComponent,
    InvoiceDetailsComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    BrowserAnimationsModule,
    FormsModule,
    ReactiveFormsModule,
    
    // Angular Material
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatToolbarModule,
    
    // Autres modules
    NgxFileDropModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }