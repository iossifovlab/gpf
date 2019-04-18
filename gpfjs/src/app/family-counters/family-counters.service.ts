import { Injectable } from '@angular/core';

import { Response, Headers, Http, RequestOptions } from '@angular/http';
import { FamilyObjectArray } from './family-counters';

import { Observable } from 'rxjs';
// import '../rxjs-operators';

import { ConfigService } from '../config/config.service';

@Injectable()
export class FamilyCountersService {
  private familyCountersUrl = "family_counters/counters";
  constructor(
    private http: Http) {}

  private getOptions(): RequestOptions {
    let options = new RequestOptions({ withCredentials: true });

    return options;
  }

  getCounters(filters: Object): Observable<FamilyObjectArray> {
    return this.http.post(this.familyCountersUrl, filters, this.getOptions())
      .map((response) => FamilyObjectArray.fromJsonArray(response.json()))
      .catch((err) => {
        console.log("Family counter:", err);
        return Observable.of(null);
      })
  }
}
