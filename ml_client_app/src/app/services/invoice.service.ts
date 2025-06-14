import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class InvoiceService {
  private apiUrl = `${environment.apiUrl}/api/invoices`;

  constructor(private http: HttpClient) { }

  // Télécharger une facture
  uploadInvoice(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('original_file', file);
    
    return this.http.post<any>(`${this.apiUrl}/upload/`, formData);
  }

  // Récupérer les résultats d'extraction d'une facture
  getInvoiceResults(invoiceId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${invoiceId}/results/`);
  }

  // Récupérer la liste des factures
  getInvoices(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  // Récupérer les détails d'une facture
  getInvoice(invoiceId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${invoiceId}/`);
  }
}