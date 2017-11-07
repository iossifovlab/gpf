import { Injectable, Injector } from '@angular/core';
import {
  Request, XHRBackend, RequestOptions, Response, Http, RequestOptionsArgs,
  Headers
} from '@angular/http';
import { Router } from '@angular/router';

import { Observable } from 'rxjs';

import { UsersService } from '../users/users.service';


@Injectable()
export class RedirectOnErrorHttpService extends Http {

  private router: Router;
  private usersService: UsersService;


  constructor(
    backend: XHRBackend,
    defaultOptions: RequestOptions,
    private injector: Injector

  ) {
    super(backend, defaultOptions);
  }

  request(url: string | Request, options?: RequestOptionsArgs): Observable<Response> {
    this.assertOrLoadServices();
    return super.request(url, options).catch((error: Response) => {
      if (error.status >= 400 && error.status < 500) {
        console.warn('redirect because of error...');
        if (error.status === 401 || error.status === 403) {
          this.usersService.getUserInfo().take(1).subscribe();
        }
        this.router.navigate(['/']);
      }
      return Observable.throw(error);
    });
  }

  private assertOrLoadServices() {
    if (!this.router) {
      this.router = this.injector.get(Router);
    }
    if (!this.usersService) {
      this.usersService = this.injector.get(UsersService);
    }
  }

}
