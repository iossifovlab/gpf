import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpHeaders, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthInterceptorService implements HttpInterceptor {
  public constructor(private authService: AuthService) { }

  public intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (this.authService.getAccessToken() !== '') {
      const headers = new HttpHeaders().set(
        'Authorization', `Bearer ${this.authService.getAccessToken()}`
      );
      return next.handle(req.clone({ headers: headers }));
    } else {
      return next.handle(req);
    }
  }
}
