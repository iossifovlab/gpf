import { Injectable } from '@angular/core';

import { Headers, Http, RequestOptions } from '@angular/http';
import { FamilyObjectArray } from './family-counters';

// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
// import '../rxjs-operators';

import { CookieService } from 'ngx-cookie';

@Injectable()
export class FamilyCountersService {
  private familyCountersUrl = 'family_counters/counters';
  constructor(
    private http: Http) {}

  private getOptions(): RequestOptions {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = new Headers({ 'X-CSRFToken': csrfToken });
    const options = new RequestOptions({ headers: headers, withCredentials: true });

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
