import { Component, EventEmitter, Output, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { InvoiceService } from '../../services/invoice.service';
import { ErrorDialogComponent } from '../error-dialog/error-dialog.component';

interface DetectedField {
  key: string;
  value: string;
}

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
  detectedFields: DetectedField[] = [];

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
      this.processDetectedFields();
    }
  }
  
  processDetectedFields(): void {
    this.detectedFields = [];
    
    // Récupérer les champs détectés automatiquement
    const detectedFields = this.structuredData?.detected_fields || {};
    
    // Convertir l'objet en tableau pour l'affichage
    for (const [key, value] of Object.entries(detectedFields)) {
      // Éviter les doublons avec les champs principaux
      if (this.isMainField(key)) {
        continue;
      }
      
      this.detectedFields.push({
        key: key,
        value: value as string
      });
    }
    
    // Trier par ordre alphabétique des clés
    this.detectedFields.sort((a, b) => a.key.localeCompare(b.key));
  }
  
  isMainField(key: string): boolean {
    // Vérifier si le champ est déjà présent dans les champs principaux
    const mainFieldKeys = ['Numéro de facture', 'Date', 'Montant total', 'Total'];
    return mainFieldKeys.some(mainKey => 
      key.toLowerCase().includes(mainKey.toLowerCase())
    );
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