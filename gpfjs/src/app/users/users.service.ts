
// tslint:disable-next-line:import-blacklist
import {throwError as observableThrowError,  Observable ,  ReplaySubject } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie';
import { User } from './users';

import { Router } from '@angular/router';
import { Location } from '@angular/common';

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
  private readonly bulkAddGroupUrl = `${this.usersUrl}/bulk_add_group`;
  private readonly bulkRemoveGroupUrl = `${this.usersUrl}/bulk_remove_group`;

  private userInfo$ = new ReplaySubject<{}>(1);
  private lastUserInfo = null;

  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService,
    private router: Router,
    private location: Location,
  ) {}

  logout(): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.logoutUrl, {}, options)
      .map(res => {
        this.router.navigate([this.location.path()]);
        return true;
      });
  }

  login(username: string, password: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.loginUrl, { username: username, password: password }, options)
      .map(res => {
        this.router.navigate([this.location.path()]);
        return true;
      })
      .catch(error => {
        return Observable.of(false);
      });
  }

  cachedUserInfo() {
    return this.lastUserInfo;
  }

  getUserInfoObservable(): Observable<any> {
    return this.userInfo$.asObservable();
  }

  getUserInfo(): Observable<any> {
    const options = { withCredentials: true };

    return this.http
      .get(this.config.baseUrl + this.userInfoUrl, options)
      .map(res => {
        return res;
      })
      .do(userInfo => {
        this.userInfo$.next(userInfo);
        this.lastUserInfo = userInfo;
      });
  }

  register(email: string, name: string, researcherId: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.registerUrl, {
      email: email,
      name: name,
      researcherId: researcherId
    }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        return observableThrowError(new Error(error.json().error_msg));
      });
  }

  resetPassword(email: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.resetPasswordUrl, { email: email }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        return observableThrowError(new Error(error.json().error_msg));
      });
  }

  changePassword(password: string, verifPath: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.changePasswordUrl, {
      password: password, verifPath: verifPath
    }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        return Observable.of(false);
      });
  }

  checkVerification(verifPath: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.checkVerificationUrl, {
      verifPath: verifPath
    }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        return Observable.of(false);
      });
  }

  getAllUsers() {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.usersUrl, options)
      .map(response => User.fromJsonArray(response));
  }

  getUser(id: number) {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.usersUrl}/${id}`;

    return this.http.get(url, options)
      .map(response => User.fromJson(response));
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

    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.usersUrl, user, options)
      .map(response => User.fromJson(response));
  }

  deleteUser(user: User) {
    if (!user.id) {
      return observableThrowError('No user id');
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;
    const options = { withCredentials: true };

    return this.http.delete(url, options);
  }

  removeUserPassword(user: User) {
    if (!user.id) {
      return observableThrowError('No user id');
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}/password_remove`;
    const options = { withCredentials: true };

    return this.http.post(url, null, options);
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
    const searchParams = new HttpParams().set('search', searchTerm);

    const options = { withCredentials: true, params: searchParams };

    return this.http.get(this.config.baseUrl + this.usersUrl, options)
      .map(response => User.fromJsonArray(response));
  }

  bulkAddGroup(users: User[], group: string) {
    const options = { withCredentials: true };

    const data = {
      userIds: users.map(u => u.id),
      group: group
    };

    return this.http.post(this.config.baseUrl + this.bulkAddGroupUrl, data, options);
  }

  bulkRemoveGroup(users: User[], group: string) {
    const options = { withCredentials: true };

    const data = {
      userIds: users.map(u => u.id),
      group: group
    };

    return this.http.post(this.config.baseUrl + this.bulkRemoveGroupUrl, data, options);
  }

}
