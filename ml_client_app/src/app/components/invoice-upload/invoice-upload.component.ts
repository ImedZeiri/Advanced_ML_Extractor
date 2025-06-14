import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Invoice } from '../../models/invoice.model';

@Component({
  selector: 'app-invoice-upload',
  templateUrl: './invoice-upload.component.html',
  styleUrls: ['./invoice-upload.component.scss']
})
export class InvoiceUploadComponent implements OnInit {
  uploadForm: FormGroup;
  selectedFiles: File[] = [];
  isUploading = false;
  uploadProgress = 0;
  uploadedInvoices: Invoice[] = [];
  errorMessage: string | null = null;

  constructor(
    private formBuilder: FormBuilder,
    private apiService: ApiService
  ) {
    this.uploadForm = this.formBuilder.group({
      files: ['']
    });
  }

  ngOnInit(): void {
  }

  onFileSelect(event: any): void {
    if (event.target.files.length > 0) {
      const files = event.target.files;
      this.selectedFiles = Array.from(files);
      this.uploadForm.get('files')?.setValue(files);
    }
  }

  onSubmit(): void {
    if (this.selectedFiles.length === 0) {
      this.errorMessage = 'Veuillez sélectionner au moins un fichier';
      return;
    }

    this.isUploading = true;
    this.errorMessage = null;

    if (this.selectedFiles.length === 1) {
      // Upload single file
      this.apiService.uploadInvoice(this.selectedFiles[0]).subscribe({
        next: (response) => {
          this.uploadedInvoices = [response];
          this.isUploading = false;
          this.resetForm();
        },
        error: (error) => {
          this.errorMessage = `Erreur lors de l'upload: ${error.message}`;
          this.isUploading = false;
        }
      });
    } else {
      // Batch upload
      this.apiService.batchUploadInvoices(this.selectedFiles).subscribe({
        next: (response) => {
          this.uploadedInvoices = response;
          this.isUploading = false;
          this.resetForm();
        },
        error: (error) => {
          this.errorMessage = `Erreur lors de l'upload: ${error.message}`;
          this.isUploading = false;
        }
      });
    }
  }

  resetForm(): void {
    this.uploadForm.reset();
    this.selectedFiles = [];
  }
}