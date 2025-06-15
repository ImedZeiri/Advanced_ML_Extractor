import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Extracteur de Factures';
  sidenavOpen = false;
  extractionData: any = null;
  fileSrc: SafeResourceUrl | null = null;
  isImage = false;

  constructor(private sanitizer: DomSanitizer) {}

  onExtractionSuccess(data: any): void {
    this.extractionData = data;
    this.sidenavOpen = true;
    
    if (data.invoice && data.invoice.file) {
      this.fileSrc = this.sanitizer.bypassSecurityTrustResourceUrl(data.invoice.file);
      
      // Vérifier si c'est une image
      const fileExt = data.invoice.file.toLowerCase().split('.').pop();
      this.isImage = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExt);
    }
  }
}