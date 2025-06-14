import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { InvoiceService } from '../../services/invoice.service';
import { Invoice } from '../../models/invoice.model';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-invoice-details',
  templateUrl: './invoice-details.component.html',
  styleUrls: ['./invoice-details.component.scss']
})
export class InvoiceDetailsComponent implements OnInit {
  invoice: Invoice | null = null;
  loading = true;
  error = false;
  pollingSubscription: Subscription | null = null;

  constructor(
    private route: ActivatedRoute,
    private invoiceService: InvoiceService
  ) {}

  ngOnInit(): void {
    const invoiceId = this.route.snapshot.paramMap.get('id');
    if (invoiceId) {
      this.loadInvoice(+invoiceId);
    }
  }

  ngOnDestroy(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
  }

  private loadInvoice(invoiceId: number): void {
    this.loading = true;
    
    // Récupération initiale des détails de la facture
    this.invoiceService.getInvoice(invoiceId).subscribe({
      next: (invoice) => {
        this.invoice = invoice;
        this.loading = false;
        
        // Si la facture est en attente ou en cours de traitement, on commence le polling
        if (invoice.status === 'pending' || invoice.status === 'processing') {
          this.startPolling(invoiceId);
        }
      },
      error: (error) => {
        this.loading = false;
        this.error = true;
        console.error('Erreur lors du chargement de la facture:', error);
      }
    });
  }

  private startPolling(invoiceId: number): void {
    // Polling toutes les 3 secondes pour vérifier l'état de traitement
    this.pollingSubscription = interval(3000)
      .pipe(
        switchMap(() => this.invoiceService.getInvoice(invoiceId))
      )
      .subscribe({
        next: (invoice) => {
          this.invoice = invoice;
          
          // Arrêt du polling si le traitement est terminé ou a échoué
          if (invoice.status === 'completed' || invoice.status === 'failed') {
            this.pollingSubscription?.unsubscribe();
            this.pollingSubscription = null;
          }
        },
        error: (error) => {
          console.error('Erreur lors du polling:', error);
          this.pollingSubscription?.unsubscribe();
          this.pollingSubscription = null;
        }
      });
  }

  getStatusClass(): string {
    if (!this.invoice) return '';
    
    switch (this.invoice.status) {
      case 'completed': return 'status-completed';
      case 'failed': return 'status-failed';
      case 'processing': return 'status-processing';
      default: return 'status-pending';
    }
  }

  getStatusText(): string {
    if (!this.invoice) return '';
    
    switch (this.invoice.status) {
      case 'completed': return 'Traitement terminé';
      case 'failed': return 'Échec du traitement';
      case 'processing': return 'En cours de traitement';
      default: return 'En attente';
    }
  }
}