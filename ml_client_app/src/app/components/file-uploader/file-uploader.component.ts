import { Component, EventEmitter, Output, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { InvoiceService } from '../../services/invoice.service';
import { ErrorDialogComponent } from '../error-dialog/error-dialog.component';
import { MatSnackBar } from '@angular/material/snack-bar';

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
  originalStructuredData: any = null;
  editMode = false;
  isSubmitting = false;
  modelAvailable = false;
  modelInfo: any = null;
  
  constructor(
    private invoiceService: InvoiceService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) { 
    this.checkModelAvailability();
  }
  
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['extractionData'] && this.extractionData) {
      this.updateStructuredData();
    }
  }
  
  updateStructuredData(): void {
    if (this.extractionData?.invoice?.extracted_content?.structured_data) {
      // Copie profonde pour garder l'original
      this.originalStructuredData = JSON.parse(JSON.stringify(this.extractionData.invoice.extracted_content.structured_data));
      this.structuredData = JSON.parse(JSON.stringify(this.extractionData.invoice.extracted_content.structured_data));
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
    this.originalStructuredData = null;

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
  
  // Nouvelles méthodes pour l'édition et l'entraînement
  
  addArticle(): void {
    if (!this.structuredData.articles) {
      this.structuredData.articles = [];
    }
    
    this.structuredData.articles.push({
      nom: '',
      quantite: null,
      prixHT: null,
      remise: null,
      totalHT: null,
      totalTTC: null
    });
  }
  
  removeArticle(index: number): void {
    this.structuredData.articles.splice(index, 1);
  }
  
  cancelEdit(): void {
    // Restaurer les données originales
    this.structuredData = JSON.parse(JSON.stringify(this.originalStructuredData));
    this.editMode = false;
  }
  
  checkModelAvailability(): void {
    this.invoiceService.checkModelAvailability().subscribe({
      next: (info) => {
        this.modelAvailable = info.model_available === true;
        this.modelInfo = info;
      },
      error: (error) => {
        console.warn('Erreur lors de la vérification de la disponibilité du modèle:', error);
        this.modelAvailable = false;
        this.modelInfo = {
          status: 'error',
          model_available: false,
          model_exists: false
        };
      }
    });
  }
  
  resetModel(): void {
    this.invoiceService.resetModel().subscribe({
      next: (response) => {
        this.snackBar.open('Modèle réinitialisé avec succès', 'Fermer', {
          duration: 5000,
          horizontalPosition: 'center',
          verticalPosition: 'bottom'
        });
        // Vérifier à nouveau la disponibilité du modèle
        this.checkModelAvailability();
      },
      error: (error) => {
        this.showErrorDialog(error.error?.message || 'Erreur lors de la réinitialisation du modèle');
      }
    });
  }

  submitCorrections(): void {
    if (!this.extractionData?.invoice?.id) {
      this.showErrorDialog('Impossible de soumettre les corrections : ID de facture manquant');
      return;
    }
    
    const invoiceId = this.extractionData.invoice.id;
    this.isSubmitting = true;
    
    // Créer un objet d'annotation avec les données originales et corrigées
    const annotationData = {
      originalData: this.originalStructuredData,
      correctedData: this.structuredData
    };
    
    this.invoiceService.submitAnnotation(invoiceId, annotationData).subscribe({
      next: (response) => {
        this.isSubmitting = false;
        this.editMode = false;
        
        // Mettre à jour les données originales avec les corrections
        this.originalStructuredData = JSON.parse(JSON.stringify(this.structuredData));
        
        // Mettre à jour les données extraites dans l'objet extractionData
        if (this.extractionData?.invoice?.extracted_content) {
          this.extractionData.invoice.extracted_content.structured_data = this.structuredData;
        }
        
        let message = 'Corrections enregistrées avec succès';
        if (response.training_job_id) {
          message += ' et entraînement du modèle lancé';
        } else if (this.modelAvailable) {
          message += ' mais l\'entraînement du modèle n\'a pas pu être lancé';
        } else {
          message += ' (mode IA avancée non disponible)';
        }
        
        // Vérifier à nouveau la disponibilité du modèle
        this.checkModelAvailability();
        
        this.snackBar.open(message, 'Fermer', {
          duration: 5000,
          horizontalPosition: 'center',
          verticalPosition: 'bottom',
          panelClass: ['success-snackbar']
        });
      },
      error: (error) => {
        this.isSubmitting = false;
        this.showErrorDialog(error.error?.message || 'Une erreur est survenue lors de la soumission des corrections');
      }
    });
  }
}