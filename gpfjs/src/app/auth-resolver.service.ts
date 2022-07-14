import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from './auth.service';
import { firstValueFrom } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class AuthResolverService implements Resolve<boolean> {

  constructor(private authService: AuthService) { }

  public resolve(route: ActivatedRouteSnapshot): Promise<boolean> {
    if (route.queryParams['code']) {
      return firstValueFrom(this.authService.requestAccessToken(route.queryParams['code']));
    }

    /* return this.usersService.getUserInfo().pipe(
      map(() => {
        return this.authService.requestAccessToken(route.queryParams['code']);
      })
    ); */
  }
}
