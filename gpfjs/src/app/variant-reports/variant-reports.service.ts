import { Injectable } from '@angular/core';
import { Http, RequestOptions } from '@angular/http';

import { Observable } from 'rxjs';

import { Studies, Study, VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';

@Injectable()
export class VariantReportsService {

  private studiesUrl = 'common_reports/studies';
  private variantsUrl = 'common_reports/studies/';
  private downloadUrl = 'common_reports/families_data/';

  constructor(
    private http: Http
  ) { }

  getStudies() {
    let options = new RequestOptions({ withCredentials: true });
    return this.http
      .get(this.studiesUrl, options)
      .map(response => Studies.fromJson(response.json()))
      .catch(error => {
        console.log(error);
        return Observable.of(null as Studies);
      });
  }

  getVariantReport(study: Study) {
    let options = new RequestOptions({ withCredentials: true });
    let url = `${this.variantsUrl}${study.name}`;
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
    return `${environment.apiPath}${this.downloadUrl}${variantReport.studyName}`;
  }

}
