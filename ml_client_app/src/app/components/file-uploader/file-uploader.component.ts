import { Component, EventEmitter, Output, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { InvoiceService } from '../../services/invoice.service';
import { ErrorDialogComponent } from '../error-dialog/error-dialog.component';

interface DetectedField {
  key: string;
  value: string;
  category?: string;
}

interface CategoryInfo {
  title: string;
  icon: string;
  color: string;
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
  categorizedFields: {[category: string]: DetectedField[]} = {};
  
  categories: {[key: string]: CategoryInfo} = {
    'vendor_info': { title: 'Informations fournisseur', icon: 'business', color: '#4caf50' },
    'client_info': { title: 'Informations client', icon: 'person', color: '#2196f3' },
    'payment_details': { title: 'Détails de paiement', icon: 'payment', color: '#ff9800' },
    'tax_details': { title: 'Informations fiscales', icon: 'receipt', color: '#f44336' },
    'product_details': { title: 'Détails des produits', icon: 'shopping_cart', color: '#9c27b0' },
    'dates': { title: 'Dates', icon: 'event', color: '#607d8b' },
    'totals': { title: 'Montants', icon: 'euro_symbol', color: '#795548' },
    'other': { title: 'Autres informations', icon: 'more_horiz', color: '#9e9e9e' }
  };
  
  // Liste des catégories à afficher dans l'ordre
  categoryOrder: string[] = [
    'vendor_info', 'client_info', 'product_details', 'totals', 
    'tax_details', 'payment_details', 'dates', 'other'
  ];

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
      this.processCategorizedFields();
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
  
  processCategorizedFields(): void {
    // Réinitialiser les catégories
    this.categorizedFields = {};
    
    // Initialiser toutes les catégories avec un tableau vide
    for (const category of this.categoryOrder) {
      this.categorizedFields[category] = [];
    }
    
    // Récupérer les champs catégorisés
    const categorized = this.structuredData?.categorized_fields || {};
    
    // Parcourir chaque catégorie
    for (const [category, fields] of Object.entries(categorized)) {
      if (typeof fields === 'object' && fields !== null) {
        // Convertir l'objet en tableau pour l'affichage
        for (const [key, value] of Object.entries(fields)) {
          this.categorizedFields[category].push({
            key: key,
            value: value as string,
            category: category
          });
        }
        
        // Trier par ordre alphabétique des clés
        this.categorizedFields[category].sort((a, b) => a.key.localeCompare(b.key));
      }
    }
  }
  
  isMainField(key: string): boolean {
    const mainFieldKeys = ['Numéro de facture', 'Date', 'Montant total', 'Total'];
    return mainFieldKeys.some(mainKey => 
      key.toLowerCase().includes(mainKey.toLowerCase())
    );
  }
  
  hasCategoryFields(category: string): boolean {
    return this.categorizedFields[category] && this.categorizedFields[category].length > 0;
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