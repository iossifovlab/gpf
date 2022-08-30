import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { BehaviorSubject, Observable, ReplaySubject } from 'rxjs';
import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';
import { DatasetsService } from 'app/datasets/datasets.service';
import { map } from 'rxjs/operators';

@Injectable()
export class VariantReportsService {
  public tags$: ReplaySubject<string[]> = new ReplaySubject<string[]>();
  private readonly variantsUrl = 'common_reports/studies/';
  private readonly downloadUrl = 'common_reports/families_data/';
  private readonly familiesUrl = 'common_reports/family_counters';
  private readonly tagsUrl = 'families/tags';
  private readonly variantsUrlWithId = 'common_reports/family_counters/download/';


  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private datasetsService: DatasetsService
  ) {
    const options = { withCredentials: true };
    const response = this.http.get(`${this.config.baseUrl}${this.tagsUrl}`, options)
      .pipe(map((data) => data));
    response.subscribe((tag: string[]) => this.tags$.next(tag));
  }

  public getVariantReport(datasetId: string): Observable<VariantReport> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.variantsUrl}${datasetId}`;
    return this.http.get(url, options).pipe(map(response => VariantReport.fromJson(response)));
  }

  public getDownloadLink(): string {
    const selectedDatasetId = this.datasetsService.getSelectedDataset().id;
    return `${environment.apiPath}${this.downloadUrl}${selectedDatasetId}`;
  }

  public getFamilies(datasetId: string, groupName:  string, counterId:  number) {
    const options = { withCredentials: true };
    const data = { study_id: datasetId, group_name: groupName, counter_id: counterId };
    const url = `${this.config.baseUrl}${this.familiesUrl}`;
    const response = this.http.post(url, data, options).pipe(map(response => response as Array<string>));
    return response;
  }

  public getTags(): Observable<string[]> {
    return this.tags$.asObservable();
  }
}
