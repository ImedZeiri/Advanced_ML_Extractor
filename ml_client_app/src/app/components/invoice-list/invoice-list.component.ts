import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { Invoice } from '../../models/invoice.model';

@Component({
  selector: 'app-invoice-list',
  templateUrl: './invoice-list.component.html',
  styleUrls: ['./invoice-list.component.scss']
})
export class InvoiceListComponent implements OnInit {
  invoices: Invoice[] = [];
  isLoading = false;
  errorMessage: string | null = null;
  
  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadInvoices();
  }
  
  loadInvoices(): void {
    this.isLoading = true;
    this.errorMessage = null;
    
    this.apiService.getInvoices().subscribe({
      next: (response) => {
        this.invoices = response.results || [];
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = `Erreur lors du chargement des factures: ${error.message}`;
        this.isLoading = false;
      }
    });
  }
  
  deleteInvoice(id: number): void {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette facture ?')) {
      this.apiService.deleteInvoice(id).subscribe({
        next: () => {
          this.invoices = this.invoices.filter(invoice => invoice.id !== id);
        },
        error: (error) => {
          this.errorMessage = `Erreur lors de la suppression: ${error.message}`;
        }
      });
    }
  }
  
  refreshList(): void {
    this.loadInvoices();
  }
}