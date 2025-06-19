import { Component, Input, OnInit } from '@angular/core';

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
  selector: 'app-invoice-display',
  templateUrl: './invoice-display.component.html',
  styleUrls: ['./invoice-display.component.scss']
})
export class InvoiceDisplayComponent implements OnInit {
  @Input() invoiceData: StructuredData | null = null;
  
  constructor() { }
  
  ngOnInit(): void {
    // S'assurer que les articles existent toujours
    if (this.invoiceData && !this.invoiceData.articles) {
      this.invoiceData.articles = [];
    }
    
    // S'assurer que le client existe toujours
    if (this.invoiceData && !this.invoiceData.client) {
      this.invoiceData.client = {
        societe: '',
        code: '',
        tva: '',
        siret: '',
        ville: '',
        pays: ''
      };
    }
  }
  
  // Méthode pour formater les montants
  formatAmount(amount: number | undefined | null): string {
    if (amount === undefined || amount === null) {
      return 'Non détecté';
    }
    return amount.toString() + ' €';
  }
  
  // Méthode pour formater les dates
  formatDate(date: string | undefined | null): string {
    if (!date) {
      return 'Non détectée';
    }
    return date;
  }
}