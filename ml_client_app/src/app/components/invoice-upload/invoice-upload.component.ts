import { Component } from '@angular/core';
import { InvoiceService } from '../../services/invoice.service';
import { Router } from '@angular/router';
import { NgxFileDropEntry, FileSystemFileEntry } from 'ngx-file-drop';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-invoice-upload',
  templateUrl: './invoice-upload.component.html',
  styleUrls: ['./invoice-upload.component.scss']
})
export class InvoiceUploadComponent {
  files: NgxFileDropEntry[] = [];
  isUploading = false;

  constructor(
    private invoiceService: InvoiceService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  dropped(files: NgxFileDropEntry[]) {
    this.files = files;
    for (const droppedFile of files) {
      if (droppedFile.fileEntry.isFile) {
        const fileEntry = droppedFile.fileEntry as FileSystemFileEntry;
        
        fileEntry.file((file: File) => {
          // Vérification du type de fichier
          if (this.isValidFileType(file)) {
            this.uploadFile(file);
          } else {
            this.snackBar.open('Format de fichier non supporté. Veuillez utiliser PDF ou image.', 'Fermer', {
              duration: 5000
            });
          }
        });
      }
    }
  }

  fileOver(event: any) {
    console.log('File over drop zone');
  }
  
  fileLeave(event: any) {
    console.log('File left drop zone');
  }

  private isValidFileType(file: File): boolean {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'];
    return allowedTypes.includes(file.type);
  }

  private uploadFile(file: File) {
    this.isUploading = true;
    
    this.invoiceService.uploadInvoice(file).subscribe({
      next: (response) => {
        this.isUploading = false;
        this.snackBar.open('Facture téléchargée avec succès!', 'Fermer', {
          duration: 3000
        });
        
        // Redirection vers la page de résultats
        this.router.navigate(['/invoices', response.id]);
      },
      error: (error) => {
        this.isUploading = false;
        this.snackBar.open('Erreur lors du téléchargement de la facture', 'Fermer', {
          duration: 5000
        });
        console.error('Erreur d\'upload:', error);
      }
    });
  }
}