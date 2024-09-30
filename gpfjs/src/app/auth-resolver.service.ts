import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from './auth.service';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class AuthResolverService {
  public constructor(
    private authService: AuthService,
  ) { }

  public resolve(route: ActivatedRouteSnapshot): Observable<object> {
    if (route.queryParams['code']) {
      return this.authService.requestAccessToken(route.queryParams['code']);
    }
  }
}
