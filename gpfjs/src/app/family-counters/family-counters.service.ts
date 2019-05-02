import { Injectable } from '@angular/core';

import { Response, Headers, Http, RequestOptions } from '@angular/http';
import { FamilyObjectArray } from './family-counters';

import { Observable } from 'rxjs';
// import '../rxjs-operators';

import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie';

@Injectable()
export class FamilyCountersService {
  private familyCountersUrl = "family_counters/counters";
  constructor(
    private http: Http,
    private cookieService: CookieService) {}

  private getOptions(): RequestOptions {
    let csrfToken = this.cookieService.get("csrftoken");
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return options;
  }

  getCounters(filters: Object): Observable<FamilyObjectArray> {
    return this.http.post(this.familyCountersUrl, filters, this.getOptions())
      .map((response) => FamilyObjectArray.fromJsonArray(response.json()))
      .catch((err) => {
        console.log('Family counter:', err);
        return Observable.of(null);
      });
  }
}
