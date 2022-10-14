import { Injectable } from '@angular/core';
import {
  HttpInterceptor, HttpRequest, HttpHandler,
  HttpHeaders, HttpEvent, HttpErrorResponse
} from '@angular/common/http';
import { Observable, Subject, throwError, catchError, switchMap, tap } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthInterceptorService implements HttpInterceptor {
  private refreshTokenInProgress = false;
  private tokenRefreshedSource = new Subject<boolean>();
  private tokenRefreshed$ = this.tokenRefreshedSource.asObservable();

  public constructor(private authService: AuthService) { }

  public intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const request = this.addAuthHeader(req);
    return next.handle(request).pipe(catchError(error => {
      return this.handleResponseError(error, request, next);
    }));
  }

  public addAuthHeader(req: HttpRequest<any>): HttpRequest<any> {
    if (this.authService.getAccessToken() !== '') {
      const headers = new HttpHeaders().set(
        'Authorization', `Bearer ${this.authService.getAccessToken()}`
      );
      return req.clone({ headers: headers });
    } else {
      return req;
    }
  }

  public handleResponseError(
    err: HttpErrorResponse, req?: HttpRequest<any>, next?: HttpHandler
  ): Observable<HttpEvent<any>> {
    if (err.status !== 401) {
      return throwError(() => err);
    }
    return this.refreshToken().pipe(
      switchMap(() => { return next.handle(this.addAuthHeader(req)); }),
    );
  }

  public refreshToken() {
    if (this.refreshTokenInProgress) {
      return new Observable(observer => {
        this.tokenRefreshed$.subscribe(() => {
          observer.next();
          observer.complete();
        });
      });
    } else {
      this.refreshTokenInProgress = true;
      return this.authService.refreshToken().pipe(
        tap(() => {
          this.refreshTokenInProgress = false;
          this.tokenRefreshedSource.next(true);
        }),
        catchError((err, caught) => {
          this.refreshTokenInProgress = false;
          throw err;
        })
      );
    }
  }
}
