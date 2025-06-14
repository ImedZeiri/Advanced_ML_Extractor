import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { Invoice, InvoiceLineItem } from '../../models/invoice.model';

@Component({
  selector: 'app-invoice-detail',
  templateUrl: './invoice-detail.component.html',
  styleUrls: ['./invoice-detail.component.scss']
})
export class InvoiceDetailComponent implements OnInit {
  invoiceId: number = 0;
  invoice: Invoice | null = null;
  isLoading = false;
  errorMessage: string | null = null;
  
  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService
  ) { }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      this.invoiceId = +params['id'];
      this.loadInvoice();
    });
  }
  
  loadInvoice(): void {
    this.isLoading = true;
    this.errorMessage = null;
    
    this.apiService.getInvoice(this.invoiceId).subscribe({
      next: (invoice) => {
        this.invoice = invoice;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = `Erreur lors du chargement de la facture: ${error.message}`;
        this.isLoading = false;
      }
    });
  }
  
  getStatusLabel(status: string): string {
    switch (status) {
      case 'pending': return 'En attente';
      case 'processing': return 'En cours';
      case 'completed': return 'Terminé';
      case 'error': return 'Erreur';
      default: return status;
    }
  }
  
  getStatusClass(status: string): string {
    return status;
  }
}