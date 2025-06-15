import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface InvoiceResponse {
  status: string;
  message: string;
  invoice: {
    id: number;
    file: string;
    uploaded_at: string;
    processed: boolean;
    extracted_content: {
      text: string;
      cleaned_text?: string;
      formatted_text?: string;
      structured_data?: any;
      extraction_method: string;
      document_type: string;
      page_count?: number;
      error?: string;
    } | null;
    formatted_text_url?: string;
    html_formatted_text_url?: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class InvoiceService {
  private apiUrl = 'http://localhost:8000/api/invoices/';

  constructor(private http: HttpClient) { }

  uploadInvoice(file: File): Observable<InvoiceResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.http.post<InvoiceResponse>(this.apiUrl, formData);
  }

  getInvoices(): Observable<any> {
    return this.http.get<any>(this.apiUrl);
  }

  getInvoice(id: number): Observable<InvoiceResponse> {
    return this.http.get<InvoiceResponse>(`${this.apiUrl}${id}/`);
  }

  reextractInvoice(id: number): Observable<InvoiceResponse> {
    return this.http.get<InvoiceResponse>(`${this.apiUrl}${id}/extract/`);
  }
}