import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface InvoiceArticle {
  nom: string | null;
  quantite: string | null;
  prixHT: string | null;
  remise: string | null;
  totalHT: string | null;
  totalTTC: string | null;
}

export interface InvoiceClient {
  societe: string | null;
  code: string | null;
  tva: string | null;
  siret: string | null;
  ville: string | null;
  pays: string | null;
}

export interface InvoiceJsonOutput {
  numeroFacture: string | null;
  numeroCommande: string | null;
  numeroContrat: string | null;
  datePiece: string | null;
  dateCommande: string | null;
  dateLivraison: string | null;
  client: InvoiceClient;
  totalTTC: string | null;
  totalHT: string | null;
  totalTVA: string | null;
  articles: InvoiceArticle[];
}

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
      json_output?: InvoiceJsonOutput;
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