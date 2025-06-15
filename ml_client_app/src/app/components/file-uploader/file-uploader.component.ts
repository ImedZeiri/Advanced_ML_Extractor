import { Component, EventEmitter, Output, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { InvoiceService } from '../../services/invoice.service';
import { ErrorDialogComponent } from '../error-dialog/error-dialog.component';

@Component({
  selector: 'app-file-uploader',
  templateUrl: './file-uploader.component.html',
  styleUrls: ['./file-uploader.component.scss']
})
export class FileUploaderComponent implements OnChanges {
  @Output() extractionSuccess = new EventEmitter<any>();
  @Input() extractionData: any = null;
  
  selectedFile: File | null = null;
  isUploading = false;
  dragOver = false;
  structuredData: any = null;

  constructor(
    private invoiceService: InvoiceService,
    private dialog: MatDialog
  ) { }
  
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['extractionData'] && this.extractionData) {
      this.updateStructuredData();
    }
  }
  
  updateStructuredData(): void {
    if (this.extractionData?.invoice?.extracted_content?.structured_data) {
      this.structuredData = this.extractionData.invoice.extracted_content.structured_data;
    }
  }

  onFileSelected(event: any): void {
    if (event.target.files) {
      this.selectedFile = event.target.files[0] ?? null;
    } else if (event.dataTransfer?.files) {
      this.selectedFile = event.dataTransfer.files[0] ?? null;
    }
  }

  onUpload(): void {
    if (!this.selectedFile) {
      this.showErrorDialog('Veuillez sélectionner un fichier');
      return;
    }

    this.isUploading = true;
    this.structuredData = null;

    this.invoiceService.uploadInvoice(this.selectedFile).subscribe({
      next: (response) => {
        this.isUploading = false;
        this.extractionSuccess.emit(response);
        this.selectedFile = null;
      },
      error: (error) => {
        this.isUploading = false;
        this.showErrorDialog(error.message || 'Une erreur est survenue lors du téléchargement');
      }
    });
  }

  showErrorDialog(message: string): void {
    this.dialog.open(ErrorDialogComponent, {
      width: '350px',
      data: { message }
    });
  }
}