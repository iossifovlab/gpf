import { Injectable } from '@angular/core';
import { Http, RequestOptions } from '@angular/http';

import { Observable } from 'rxjs';

import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';

@Injectable()
export class VariantReportsService {

  private variantsUrl = 'common_reports/studies/';
  private downloadUrl = 'common_reports/families_data/';

  constructor(
    private http: Http
  ) { }

  getVariantReport(datasetId: string): Observable<VariantReport> {
    let options = new RequestOptions({ withCredentials: true });
    let url = `${this.variantsUrl}${datasetId}`;
    return this.http
      .get(url, options)
      .map(response => {
        return VariantReport.fromJson(response.json());
      })
      .catch(error => {
        console.log(error);
        return Observable.of(null as VariantReport);
      });
  }

  getDownloadLink(variantReport: VariantReport) {
    return `${environment.apiPath}${this.downloadUrl}${variantReport.id}`;
  }

}
