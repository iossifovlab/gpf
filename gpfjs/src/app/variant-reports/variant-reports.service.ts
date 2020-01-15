import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';

@Injectable()
export class VariantReportsService {
  private readonly variantsUrl = 'common_reports/studies/';
  private readonly downloadUrl = 'common_reports/families_data/';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getVariantReport(datasetId: string): Observable<VariantReport> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.variantsUrl}${datasetId}`;

    return this.http
      .get(url, options)
      .map(response => {
        return VariantReport.fromJson(response);
      });
  }

  getDownloadLink(variantReport: VariantReport) {
    return `${environment.apiPath}${this.downloadUrl}${variantReport.id}`;
  }
}
