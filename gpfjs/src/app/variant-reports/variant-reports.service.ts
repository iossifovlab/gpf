import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';
import { DatasetsService } from 'app/datasets/datasets.service';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { AuthService } from 'app/auth.service';

@Injectable()
export class VariantReportsService {
  private readonly variantsUrl = 'common_reports/studies/';
  private readonly downloadUrl = 'common_reports/families_data/';
  private readonly familiesUrl = 'common_reports/family_counters';
  private readonly tagsUrl = 'families/tags';
  private readonly pedigreeDownloadUrl = 'common_reports/family_counters/download';

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private datasetsService: DatasetsService,
    private cookieService: CookieService,
    private authService: AuthService,
  ) { }

  public getVariantReport(datasetId: string): Observable<VariantReport> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.variantsUrl}${datasetId}`;
    return this.http.get(url, options).pipe(map(response => VariantReport.fromJson(response)));
  }

  private getDownloadLink(): string {
    const selectedDatasetId = this.datasetsService.getSelectedDataset().id;
    return `${environment.apiPath}${this.downloadUrl}${selectedDatasetId}`;
  }

  public downloadFamilies(): Promise<Response> {
    return fetch(this.getDownloadLink(), {
      headers: {'Authorization': `Bearer ${this.authService.getAccessToken()}`}
    });
  }

  public getFamilies(datasetId: string, groupName: string, counterId: number): Observable<string[]> {
    const options = { withCredentials: true };
    const data = { study_id: datasetId, group_name: groupName, counter_id: counterId };
    const url = `${this.config.baseUrl}${this.familiesUrl}`;
    const response = this.http.post(url, data, options).pipe(map(response => response as Array<string>));
    return response;
  }

  public getTags(): Observable<object> {
    const options = { withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.tagsUrl}`, options);
  }

  public downloadPedigreeCount(params): Promise<Response> {
    const headers = {'Content-Type': 'application/json'};
    headers['Authorization'] = `Bearer ${this.authService.getAccessToken()}`;
    return fetch(`${environment.apiPath}${this.pedigreeDownloadUrl}`, {
      method: 'POST',
      credentials: 'include',
      headers: headers,
      body: JSON.stringify(params)
    });
  }

  public async downloadPedigreeTags(studyId: string, tags: string): Promise<Response> {
    let url = `${this.config.baseUrl}${this.downloadUrl}${studyId}`;

    if (tags) {
      url = `${url}?${new URLSearchParams({'tags': tags})}`;
    }

    const headers = {
      'X-CSRFToken': this.cookieService.get('csrftoken'),
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.authService.getAccessToken()}`
    };

    return fetch(url, {
      credentials: 'include',
      headers: headers,
    });
  }
}
