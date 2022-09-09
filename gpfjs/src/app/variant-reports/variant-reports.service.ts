import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';
import { DatasetsService } from 'app/datasets/datasets.service';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';

@Injectable()
export class VariantReportsService {
  private readonly variantsUrl = 'common_reports/studies/';
  private readonly downloadUrl = 'common_reports/families_data/';
  private readonly familiesUrl = 'common_reports/family_counters';
  private readonly tagsUrl = 'families/tags';

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private datasetsService: DatasetsService,
    private cookieService: CookieService,
  ) { }

  public getVariantReport(datasetId: string): Observable<VariantReport> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.variantsUrl}${datasetId}`;
    return this.http.get(url, options).pipe(map(response => VariantReport.fromJson(response)));
  }

  public getDownloadLink(): string {
    const selectedDatasetId = this.datasetsService.getSelectedDataset().id;
    return `${environment.apiPath}${this.downloadUrl}${selectedDatasetId}`;
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

  public async getDownloadLinkPedigreeTags(study_id: string, tags: string) {
    const searchParams = new HttpParams().set('study_id', study_id).set('tags', tags);
    const options = { headers: this.getHeaders(), withCredentials: true, params: searchParams };
    const result = await this.http.get(`${this.config.baseUrl}${this.downloadUrl}download`, { ...options, responseType: 'blob' })
      .subscribe(async res => {
        if (tags) {
          const a = document.createElement('a');
          a.href = URL.createObjectURL(res);
          a.download = 'families.ped';
          const text = await res.text();
          if (text && text !== ' ' && text !== '\n') {
            a.click();
          }
        } else {
          const a = document.createElement('a');
          a.href = this.getDownloadLink();
          a.download = 'families.ped';
          a.click();
        }
      });
    return result;
  }

  private getHeaders() {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' };

    return headers;
  }
}
