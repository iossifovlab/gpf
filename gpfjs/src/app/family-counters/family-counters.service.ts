import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FamilyObjectArray } from './family-counters';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { CookieService } from 'ngx-cookie';
import { ConfigService } from 'app/config/config.service';

@Injectable()
export class FamilyCountersService {
  private readonly familyCountersUrl = 'family_counters/counters';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService
  ) {}

  private getOptions() {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return options;
  }

  getCounters(filters: Object): Observable<FamilyObjectArray> {
    return this.http.post(this.config.baseUrl + this.familyCountersUrl, filters, this.getOptions())
      .map((response: any) => FamilyObjectArray.fromJsonArray(response))
      .catch((err) => {
        console.log('Family counter:', err);
        return Observable.of(null);
      });
  }
}
