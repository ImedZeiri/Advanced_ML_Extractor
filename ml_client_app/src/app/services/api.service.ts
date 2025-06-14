import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Invoice, InvoiceTemplate, TrainingData } from '../models/invoice.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Invoice endpoints
  getInvoices(): Observable<any> {
    return this.http.get(`${this.apiUrl}/invoices/`);
  }

  getInvoice(id: number): Observable<Invoice> {
    return this.http.get<Invoice>(`${this.apiUrl}/invoices/${id}/`);
  }

  uploadInvoice(file: File): Observable<Invoice> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.http.post<Invoice>(`${this.apiUrl}/invoices/`, formData);
  }

  batchUploadInvoices(files: File[]): Observable<Invoice[]> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    return this.http.post<Invoice[]>(`${this.apiUrl}/invoices/batch_process/`, formData);
  }

  deleteInvoice(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/invoices/${id}/`);
  }

  // Template endpoints
  getTemplates(): Observable<any> {
    return this.http.get(`${this.apiUrl}/templates/`);
  }

  getTemplate(id: number): Observable<InvoiceTemplate> {
    return this.http.get<InvoiceTemplate>(`${this.apiUrl}/templates/${id}/`);
  }

  createTemplate(template: InvoiceTemplate): Observable<InvoiceTemplate> {
    return this.http.post<InvoiceTemplate>(`${this.apiUrl}/templates/`, template);
  }

  updateTemplate(template: InvoiceTemplate): Observable<InvoiceTemplate> {
    return this.http.put<InvoiceTemplate>(`${this.apiUrl}/templates/${template.id}/`, template);
  }

  deleteTemplate(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/templates/${id}/`);
  }

  // Training data endpoints
  getTrainingData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/training-data/`);
  }

  uploadTrainingData(file: File, datasetType: string, annotations?: any): Observable<TrainingData> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataset_type', datasetType);
    
    if (annotations) {
      formData.append('annotations', JSON.stringify(annotations));
    }
    
    return this.http.post<TrainingData>(`${this.apiUrl}/training-data/`, formData);
  }

  importDataset(datasetType: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/training-data/import_dataset/`, { dataset_type: datasetType });
  }

  trainModel(datasetType: string, modelName: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/training-data/train_model/`, {
      dataset_type: datasetType,
      model_name: modelName
    });
  }
}