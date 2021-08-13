import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';
import { DatasetsService } from 'app/datasets/datasets.service';
import { map } from 'rxjs/operators';

@Injectable()
export class VariantReportsService {
  private readonly variantsUrl = 'common_reports/studies/';
  private readonly downloadUrl = 'common_reports/families_data/';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private datasetsService: DatasetsService
  ) {}

  getVariantReport(datasetId: string): Observable<VariantReport> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.variantsUrl}${datasetId}`;

    return this.http.get(url, options).pipe(
      map(response => {
        return VariantReport.fromJson(response);
      })
    );
  }

  getDownloadLink() {
    const selectedDatasetId = this.datasetsService.getSelectedDatasetId();
    return `${environment.apiPath}${this.downloadUrl}${selectedDatasetId}`;
  }
}
