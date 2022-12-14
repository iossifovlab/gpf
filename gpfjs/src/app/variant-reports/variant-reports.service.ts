import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams, HttpResponse } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { Observable, Subscription } from 'rxjs';
import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';
import { DatasetsService } from 'app/datasets/datasets.service';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { downloadBlobResponse } from 'app/utils/blob-download';

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

  public downloadFamilies(): Observable<HttpResponse<Blob>> {
    return this.http.get(this.getDownloadLink(), {observe: 'response', responseType: 'blob'});
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

  public downloadPedigreeCount(json): Observable<HttpResponse<Blob>> {
    return this.http.post(`${environment.apiPath}${this.pedigreeDownloadUrl}`,
      json, {
        observe: 'response', headers: new HttpHeaders({ 'Content-Type': 'application/json'}), responseType: 'blob'
      });
  }

  public async getDownloadLinkPedigreeTags(studyId: string, tags: string): Promise<Subscription> {
    let searchParams: HttpParams;

    if (tags) {
      searchParams = new HttpParams().set('tags', tags);
    }

    const headers = {
      'X-CSRFToken': this.cookieService.get('csrftoken'),
      'Content-Type': 'application/json'
    };

    return this.http.get(`${this.config.baseUrl}${this.downloadUrl}${studyId}`,
      { headers: headers, withCredentials: true, params: searchParams, observe: 'response', responseType: 'blob'})
      .subscribe(res => {
        downloadBlobResponse(res, 'families.ped');
      });
  }
}
