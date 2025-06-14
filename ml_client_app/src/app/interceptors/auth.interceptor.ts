import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor
} from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private authService: AuthService) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Get the auth token from the service
    const currentUser = this.authService.currentUserValue;
    
    if (currentUser && currentUser.token) {
      // Clone the request and add the authorization header
      request = request.clone({
        setHeaders: {
          Authorization: `Token ${currentUser.token}`
        }
      });
    }
    
    return next.handle(request);
  }
}