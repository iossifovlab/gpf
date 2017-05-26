import { Injectable } from '@angular/core';
import { Http } from '@angular/http';

import { Observable } from 'rxjs';

import { Studies } from './variant-reports';

@Injectable()
export class VariantReportsService {

  private studiesUrl = 'common_reports/report_studies';

  constructor(
    private http: Http
  ) { }

  getStudies() {
    return this.http
      .get(this.studiesUrl)
      .map(response => Studies.fromJson(response.json()))
      .catch(error => {
        console.log(error);
        return Observable.of(null as Studies);
      });
  }

}
