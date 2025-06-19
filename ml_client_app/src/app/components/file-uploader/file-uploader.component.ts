import {
  Component,
  EventEmitter,
  Output,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSidenav } from '@angular/material/sidenav';
import { InvoiceService } from '../../services/invoice.service';
import { ErrorDialogComponent } from '../error-dialog/error-dialog.component';

interface Article {
  nom: string;
  quantite: number;
  prixHT: number;
  remise: number;
  totalHT: number;
  totalTTC: number;
}

interface Client {
  societe: string;
  code: string;
  tva: string;
  siret: string;
  ville: string;
  pays: string;
}

interface StructuredData {
  numeroFacture: string;
  numeroCommande: number;
  numeroContrat: string;
  datePiece: string;
  dateCommande: string;
  dateLivraison: string;
  client: Client;
  totalTTC: number;
  totalHT: number;
  totalTVA: number;
  articles: Article[];
}

@Component({
  selector: 'app-file-uploader',
  templateUrl: './file-uploader.component.html',
  styleUrls: ['./file-uploader.component.scss'],
})
export class FileUploaderComponent implements OnChanges {
  @Output() extractionSuccess = new EventEmitter<any>();
  @Input() extractionData: any = null;

  // Référence aux sidenavs
  @ViewChild('pdfSidenav') pdfSidenav!: MatSidenav;
  @ViewChild('resultSidenav') resultSidenav!: MatSidenav;

  selectedFile: File | null = null;
  isUploading = false;
  isLoading = false;
  dragOver = false;
  structuredData: StructuredData | null = null;
  pdfUrl: string | null = null;
  isExpanded = false;
  displayedColumns: string[] = [
    'nom',
    'quantite',
    'prixHT',
    'remise',
    'totalHT',
    'totalTTC',
  ];

  constructor(
    private invoiceService: InvoiceService,
    private dialog: MatDialog
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['extractionData'] && this.extractionData) {
      this.updateStructuredData();
      if (this.extractionData.invoice?.file) {
        this.pdfUrl = this.extractionData.invoice.file;
      }

      // Ouvrir le sidenav automatiquement quand les données sont disponibles
      if (this.structuredData && this.resultSidenav) {
        this.isLoading = false;
        this.resultSidenav.open();
      }
    }
  }

  updateStructuredData(): void {
    if (this.extractionData?.invoice?.extracted_content?.structured_data) {
      this.structuredData =
        this.extractionData.invoice.extracted_content.structured_data;
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
    this.pdfUrl = null;

    this.isLoading = true;

    this.invoiceService.uploadInvoice(this.selectedFile).subscribe({
      next: (response) => {
        this.isUploading = false;
        this.extractionSuccess.emit(response);
        this.selectedFile = null;
        if (this.resultSidenav) {
          this.resultSidenav.open();
        }
      },
      error: (error) => {
        this.isUploading = false;
        this.isLoading = false;
        if (this.resultSidenav) {
          this.resultSidenav.close();
        }
        this.showErrorDialog(
          error.message || 'Une erreur est survenue lors du téléchargement'
        );
      },
    });
  }

  showErrorDialog(message: string): void {
    this.dialog.open(ErrorDialogComponent, {
      width: '350px',
      data: { message },
    });
  }

  toggleExpand(): void {
    this.isExpanded = !this.isExpanded;
  }
}
