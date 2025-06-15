import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Extracteur de Factures';
  sidenavOpen = false;
  extractionData: any = null;

  onExtractionSuccess(data: any): void {
    this.extractionData = data;
    this.sidenavOpen = true;
  }
}