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
import { trigger, state, style, animate, transition } from '@angular/animations';

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
  animations: [
    trigger('expandCollapse', [
      state('expanded', style({
        width: '50%',
        opacity: 1
      })),
      state('collapsed', style({
        width: '0%',
        opacity: 0,
        display: 'none'
      })),
      transition('collapsed => expanded', [
        style({ display: 'block' }),
        animate('300ms ease-out')
      ]),
      transition('expanded => collapsed', [
        animate('300ms ease-in', style({ width: '0%', opacity: 0 })),
        style({ display: 'none' })
      ])
    ]),
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-out', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ opacity: 0 }))
      ])
    ])
  ]
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
  showPdf = false;
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
    
    // Si on réduit la vue, masquer immédiatement le PDF
    if (!this.isExpanded) {
      this.showPdf = false;
    }
    
    // Ajout d'une classe temporaire pour l'animation
    const container = document.querySelector('.result-container');
    if (container) {
      container.classList.add('animating');
      
      setTimeout(() => {
        container.classList.remove('animating');
        
        // Afficher le PDF après la fin de l'animation si on est en mode expansion
        if (this.isExpanded) {
          this.showPdf = true;
        }
      }, 300); // Durée de l'animation
    }
  }
}
