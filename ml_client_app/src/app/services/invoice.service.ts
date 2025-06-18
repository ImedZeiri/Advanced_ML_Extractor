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
      confidence_scores?: {
        [key: string]: number;
      };
    } | null;
    formatted_text_url?: string;
    html_formatted_text_url?: string;
  };
}

export interface AnnotationData {
  originalData: any;
  correctedData: any;
}

export interface TrainingResponse {
  status: string;
  message: string;
  training_job_id?: string;
  model_updated?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class InvoiceService {
  private apiUrl = 'http://localhost:8000/api/invoices/';
  private mlApiUrl = 'http://localhost:8000/api/ml/';

  constructor(private http: HttpClient) {}

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

  // Nouvelles méthodes pour l'annotation et l'entraînement

  submitAnnotation(
    invoiceId: number,
    annotationData: AnnotationData
  ): Observable<TrainingResponse> {
    return this.http.post<TrainingResponse>(
      `${this.apiUrl}${invoiceId}/annotate/`,
      annotationData
    );
  }

  getTrainingStatus(trainingJobId: string): Observable<TrainingResponse> {
    return this.http.get<TrainingResponse>(
      `${this.mlApiUrl}training-status/${trainingJobId}/`
    );
  }

  getModelInfo(): Observable<any> {
    return this.http.get<any>(`${this.mlApiUrl}model-info/`);
  }

  checkModelAvailability(): Observable<any> {
    return this.http.get<any>(`${this.mlApiUrl}model-info/`);
  }
  exportAnnotations(): Observable<any> {
    return this.http.get<any>(`${this.mlApiUrl}export-annotations/`);
  }
  
  resetModel(): Observable<any> {
    return this.http.post<any>(`${this.mlApiUrl}reset-model/`, {});
  }
}
