
// tslint:disable-next-line:import-blacklist
import {throwError as observableThrowError, Observable, Subject, ReplaySubject, of } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie-service';
import { User } from './users';

import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { Store } from '@ngxs/store';
import { StateResetAll } from 'ngxs-reset-plugin';
import { catchError, map, tap } from 'rxjs/operators';

const oboe = require('oboe');

@Injectable()
export class UsersService {
  private readonly logoutUrl = 'users/logout';
  private readonly loginUrl = 'users/login';
  private readonly userInfoUrl = 'users/get_user_info';
  private readonly registerUrl = 'users/register';
  private readonly resetPasswordUrl = 'users/reset_password';
  private readonly changePasswordUrl = 'users/change_password';
  private readonly checkVerificationUrl = 'users/check_verif_path';
  private readonly usersUrl = 'users';
  private readonly usersStreamingUrl = `${this.usersUrl}/streaming_search`;
  private readonly bulkAddGroupsUrl = `${this.usersUrl}/bulk_add_groups`;
  private readonly bulkRemoveGroupsUrl = `${this.usersUrl}/bulk_remove_groups`;

  private userInfo$ = new ReplaySubject<{}>(1);
  private lastUserInfo = null;

  private oboeInstance = null;
  private connectionEstablished = false;
  public usersStreamingFinishedSubject = new Subject();

  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService,
    private router: Router,
    private location: Location,
    private store: Store,
  ) {}

  logout(): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.logoutUrl, {}, options).pipe(
      map(() => {
        this.router.navigate([this.location.path()]);
        this.store.dispatch(new StateResetAll());
        return true;
      })
    );
  }

  login(username: string, password?: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };
    const request = { username: username };

    if (password) {
      request['password'] = password;
    }

    return this.http.post(this.config.baseUrl + this.loginUrl, request, options).pipe(
      map(() => {
        this.router.navigate([this.location.path()]);
        return true;
      }),
      catchError(error => {
        return of(error);
      })
    )
  }

  cachedUserInfo() {
    return this.lastUserInfo;
  }

  getUserInfoObservable(): Observable<any> {
    return this.userInfo$.asObservable();
  }

  getUserInfo(): Observable<any> {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.userInfoUrl, options).pipe(
      map(res => {
        return res;
      }),
      tap(userInfo => {
        this.userInfo$.next(userInfo);
        this.lastUserInfo = userInfo;
      })
    );
  }

  isEmailValid(email: string): boolean {
    const re = new RegExp(
      "[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{" +
      "|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?" +
      ":[a-z0-9-]*[a-z0-9])?"
    );
    return re.test(String(email).toLowerCase());
  }

  isNameValid(name: string): boolean {
    return !(name === undefined || name === '');
  }

  register(email: string, name: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    if (!this.isEmailValid(email)) {
      return observableThrowError(new Error(
        'Invalid email address entered. Please use a valid email address.'
      ));
    }

    if (!this.isNameValid(name)) {
      return observableThrowError(new Error(
        'Name field cannot be empty.'
      ));
    }

    return this.http.post(this.config.baseUrl + this.registerUrl, {
      email: email,
      name: name,
    }, options).pipe(
      map(() => {
        return true;
      }),
      catchError(error => {
        return observableThrowError(new Error(error.error.error_msg));
      })
    );
  }

  resetPassword(email: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.resetPasswordUrl, { email: email }, options).pipe(
      map(() => {
        return true;
      }),
      catchError(error => {
        return observableThrowError(new Error(error.error.error_msg));
      })
    );
  }

  changePassword(password: string, verifPath: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.changePasswordUrl, {
      password: password, verifPath: verifPath
    }, options).pipe(
      map(() => {
        return true;
      }),
      catchError(() => {
        return of(false);
      })
    );
  }

  checkVerification(verifPath: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.checkVerificationUrl, {
      verifPath: verifPath
    }, options).pipe(
      map(() => {
        return true;
      }),
      catchError(() => {
        return of(false);
      })
    );
  }

  getAllUsers() {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.usersUrl, options).pipe(
      map(response => User.fromJsonArray(response))
    );
  }

  getUser(id: number) {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.usersUrl}/${id}`;

    return this.http.get(url, options).pipe(
      map(response => User.fromJson(response))
    );
  }

  updateUser(user: User) {
    const dto = {
      id: user.id,
      name: user.name,
      groups: user.groups,
      hasPassword: user.hasPassword,
    };
    if (!user.id) {
      return observableThrowError('Unknown id...');
    }
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;

    return this.http.put(url, dto, options);
  }

  createUser(user: User) {
    if (user.id) {
      return observableThrowError('Create should not have user id');
    }

    if (!this.isEmailValid(user.email)) {
      return observableThrowError(new Error(
        'Invalid email address entered. Please use a valid email address.'
      ));
    }

    if (!this.isNameValid(user.name)) {
      return observableThrowError(new Error(
        'Name field cannot be empty.'
      ));
    }

    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.usersUrl, user, options).pipe(
      map(response => User.fromJson(response)),
      catchError(error => {
        return observableThrowError(new Error(error.error.email));
      })
    );
  }

  deleteUser(user: User) {
    if (!user.id) {
      return observableThrowError('No user id');
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;
    const options = { withCredentials: true };

    return this.http.delete(url, options);
  }

  resetUserPassword(user: User) {
    if (!user.id) {
      return observableThrowError('No user id');
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}/password_reset`;
    const options = { withCredentials: true };

    return this.http.post(url, null, options);
  }

  removeUserGroup(user: User, group: string) {
    const clone = user.clone();
    clone.groups = clone.groups.filter(grp => grp !== group);
    return this.updateUser(clone);
  }

  searchUsersByGroup(searchTerm: string) {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const usersSubject: Subject<User> = new Subject()

    let url;
    if(searchTerm !== null) {
      const searchParams = new HttpParams().set('search', searchTerm);
      url = `${this.config.baseUrl}${this.usersStreamingUrl}?${searchParams.toString()}`;
    }
    else {
      url = `${this.config.baseUrl}${this.usersStreamingUrl}`;
    }

    this.oboeInstance = oboe({
      url: url,
      method: "GET",
      headers: headers,
      withCredentials: true,
    }).start(data => {
      this.connectionEstablished = true;
      this.usersStreamingFinishedSubject.next(false);
    }).node('!.*', data => {
      usersSubject.next(data);
    }).done(data => {
      this.usersStreamingFinishedSubject.next(true);
    }).fail(error => {
      this.connectionEstablished = false;
      this.usersStreamingFinishedSubject.next(true);
      console.warn('oboejs encountered a fail event while streaming');
    });

    return usersSubject.map(data => { return User.fromJson(data); });
  }

  bulkAddGroups(users: User[], groups: string[]) {
    const options = { withCredentials: true };

    const data = {
      userIds: users.map(u => u.id),
      groups: groups
    };

    return this.http.post(this.config.baseUrl + this.bulkAddGroupsUrl, data, options);
  }

  bulkRemoveGroups(users: User[], groups: string[]) {
    const options = { withCredentials: true };

    const data = {
      userIds: users.map(u => u.id),
      groups: groups
    };

    return this.http.post(this.config.baseUrl + this.bulkRemoveGroupsUrl, data, options);
  }

}
