import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions, URLSearchParams } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';
import { ReplaySubject } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie';
import { User } from './users';

@Injectable()
export class UsersService {
  private logoutUrl = 'users/logout';
  private loginUrl = 'users/login';
  private userInfoUrl = 'users/get_user_info';
  private registerUrl = 'users/register';
  private resetPasswordUrl = 'users/reset_password';
  private changePasswordUrl = 'users/change_password';
  private checkVerificationUrl = 'users/check_verif_path';
  private usersUrl = 'users';
  private bulkAddGroupUrl = `${this.usersUrl}/bulk_add_group`;
  private bulkRemoveGroupUrl = `${this.usersUrl}/bulk_remove_group`;

  private userInfo$ = new ReplaySubject<{}>(1);
  private lastUserInfo = null;

  constructor(
    private http: Http,
    private config: ConfigService,
    private cookieService: CookieService
  ) {

  }

  logout(): Observable<boolean> {
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.logoutUrl, {}, options)
      .map(res => {
        return true;
      });
  }

  login(username: string, password: string): Observable<boolean> {
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.loginUrl, { username: username, password: password }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        return Observable.of(false);
      });
  }

  cachedUserInfo() {
    return this.lastUserInfo;
  }

  getUserInfoObservable() {
    return this.userInfo$.asObservable();
  }

  getUserInfo(): Observable<any> {
    let options = new RequestOptions({ withCredentials: true });

    return this.http
      .get(this.userInfoUrl, options)
      .map(res => {
        return res.json();
      })
      .do(userInfo => {
        this.userInfo$.next(userInfo);
        this.lastUserInfo = userInfo;
      });
  }

  register(email: string, name: string, researcherId: string): Observable<boolean> {
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.registerUrl, {
      email: email,
      name: name,
      researcherId: researcherId
    }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        throw new Error(error.json().error_msg);
      });
  }

  resetPassword(email: string): Observable<boolean> {
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.resetPasswordUrl, { email: email }, options)
      .map(res => {
        return true;
      })
      .catch(error => {
        throw new Error(error.json().error_msg);
      });
  }

  changePassword(password: string, verifPath: string): Observable<boolean> {
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.changePasswordUrl, {
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
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.checkVerificationUrl, {
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
    let options = new RequestOptions({ withCredentials: true });

    return this.http.get(this.usersUrl, options)
      .map(response => User.fromJsonArray(response.json()));
  }

  getUser(id: number) {
    let options = new RequestOptions({ withCredentials: true });
    let url = `${this.usersUrl}/${id}`;

    return this.http.get(url, options)
      .map(response => User.fromJson(response.json()));
  }

  updateUser(user: User) {
    let dto = {
      id: user.id,
      name: user.name,
      groups: user.groups,
      hasPassword: user.hasPassword,
    };
    if (!user.id) {
      return Observable.throw('Unknown id...');
    }
    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({
      headers: headers,
      withCredentials: true
    });
    let url = `${this.usersUrl}/${user.id}`;

    return this.http.put(url, dto, options);
  }

  createUser(user: User) {
    if (user.id) {
      return Observable.throw('Create should not have user id');
    }

    let csrfToken = this.cookieService.get('csrftoken');
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({
      headers: headers,
      withCredentials: true
    });

    return this.http.post(this.usersUrl, user, options)
      .map(response => User.fromJson(response.json()));
  }

  deleteUser(user: User) {
    if (!user.id) {
      return Observable.throw('No user id');
    }
    let url = `${this.usersUrl}/${user.id}`;
    let options = new RequestOptions({ withCredentials: true });

    return this.http.delete(url, options);
  }

  removeUserPassword(user: User) {
    if (!user.id) {
      return Observable.throw('No user id');
    }
    let url = `${this.usersUrl}/${user.id}/password_remove`;
    let options = new RequestOptions({ withCredentials: true });

    return this.http.post(url, null, options);
  }

  resetUserPassword(user: User) {
    if (!user.id) {
      return Observable.throw('No user id');
    }
    let url = `${this.usersUrl}/${user.id}/password_reset`;
    let options = new RequestOptions({ withCredentials: true });

    return this.http.post(url, null, options);
  }

  removeUserGroup(user: User, group: string) {
    let clone = user.clone();
    clone.groups = clone.groups.filter(grp => grp !== group);
    return this.updateUser(clone);
  }

  searchUsersByGroup(searchTerm: string) {
    let searchParams = new URLSearchParams();
    searchParams.set('search', searchTerm);

    let options = new RequestOptions({
      withCredentials: true,
      search: searchParams
    });

    return this.http.get(this.usersUrl, options)
      .map(response => User.fromJsonArray(response.json()));
  }

  bulkAddGroup(users: User[], group: string) {
    let options = new RequestOptions({ withCredentials: true });

    let data = {
      userIds: users.map(u => u.id),
      group: group
    };

    return this.http.post(this.bulkAddGroupUrl, data, options);
  }

  bulkRemoveGroup(users: User[], group: string) {
    let options = new RequestOptions({ withCredentials: true });

    let data = {
      userIds: users.map(u => u.id),
      group: group
    };

    return this.http.post(this.bulkRemoveGroupUrl, data, options);
  }

}
