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
  isEditable = false;
  newArticle: Article = {
    nom: '',
    quantite: 0,
    prixHT: 0,
    remise: 0,
    totalHT: 0,
    totalTTC: 0
  };
  
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
  
  // Méthode pour basculer le mode édition
  toggleEditMode(): void {
    this.isEditable = !this.isEditable;
  }
  
  // Méthode pour ajouter un nouvel article
  addArticle(): void {
    if (!this.invoiceData) return;
    
    // Calculer les totaux
    this.newArticle.totalHT = this.newArticle.quantite * this.newArticle.prixHT * (1 - this.newArticle.remise / 100);
    this.newArticle.totalTTC = this.newArticle.totalHT * 1.2; // TVA à 20% par défaut
    
    // Ajouter l'article
    this.invoiceData.articles.push({...this.newArticle});
    
    // Recalculer les totaux de la facture
    this.recalculateInvoiceTotals();
    
    // Réinitialiser le nouvel article
    this.newArticle = {
      nom: '',
      quantite: 0,
      prixHT: 0,
      remise: 0,
      totalHT: 0,
      totalTTC: 0
    };
  }
  
  // Méthode pour supprimer un article
  removeArticle(index: number): void {
    if (!this.invoiceData) return;
    
    this.invoiceData.articles.splice(index, 1);
    this.recalculateInvoiceTotals();
  }
  
  // Méthode pour recalculer les totaux de la facture
  recalculateInvoiceTotals(): void {
    if (!this.invoiceData) return;
    
    this.invoiceData.totalHT = this.invoiceData.articles.reduce((sum, article) => sum + article.totalHT, 0);
    this.invoiceData.totalTTC = this.invoiceData.articles.reduce((sum, article) => sum + article.totalTTC, 0);
    this.invoiceData.totalTVA = this.invoiceData.totalTTC - this.invoiceData.totalHT;
  }
  
  // Méthode pour mettre à jour les totaux d'un article
  updateArticleTotals(article: Article): void {
    article.totalHT = article.quantite * article.prixHT * (1 - article.remise / 100);
    article.totalTTC = article.totalHT * 1.2; // TVA à 20% par défaut
    this.recalculateInvoiceTotals();
  }
}