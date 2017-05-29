import { Injectable } from '@angular/core';
import { Http } from '@angular/http';

import { Observable } from 'rxjs';

import { Studies, Study, VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';

@Injectable()
export class VariantReportsService {

  private studiesUrl = 'common_reports/report_studies';
  private variantsUrl = 'common_reports/variant_reports/';
  private downloadUrl = 'common_reports/families_data/';

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

  getVariantReport(study: Study) {
    let url = `${this.variantsUrl}${study.name}`;
    return this.http
      .get(url)
      .map(response => VariantReport.fromJson(response.json()))
      .catch(error => {
        console.log(error);
        return Observable.of(null as VariantReport);
      });
  }

  getDownloadLink(variantReport: VariantReport) {
    return `${environment.apiPath}${this.downloadUrl}${variantReport.studyName}`;
  }

}
