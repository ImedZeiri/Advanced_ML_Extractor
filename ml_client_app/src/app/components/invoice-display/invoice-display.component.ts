import { Component, Input } from '@angular/core';

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
export class InvoiceDisplayComponent {
  @Input() invoiceData: StructuredData | null = null;
  
  constructor() { }
  
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
  
  // Méthode pour vérifier si une valeur est définie
  isDefined(value: any): boolean {
    return value !== undefined && value !== null && value !== '';
  }
}