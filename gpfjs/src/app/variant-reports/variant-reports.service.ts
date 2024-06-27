import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { VariantReport } from './variant-reports';
import { environment } from '../../environments/environment';
import { map } from 'rxjs/operators';
import { Store } from '@ngxs/store';
import { DatasetModel } from 'app/datasets/datasets.state';

@Injectable()
export class VariantReportsService {
  private readonly variantsUrl = 'common_reports/studies/';
  private readonly downloadUrl = 'common_reports/families_data/';
  private readonly familiesUrl = 'common_reports/family_counters';
  private readonly tagsUrl = 'families/tags';

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private store: Store
  ) { }

  public getVariantReport(datasetId: string): Observable<VariantReport> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.variantsUrl}${datasetId}`;
    return this.http.get(url, options).pipe(map(response => VariantReport.fromJson(response)));
  }

  public getDownloadLink(): string {
    let selectedDatasetId = '';
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).subscribe(state => {
      selectedDatasetId = state.selectedDataset.id;
    });
    return `${environment.apiPath}${this.downloadUrl}${selectedDatasetId}`;
  }

  public getFamilies(datasetId: string, groupName: string, counterId: number): Observable<string[]> {
    const options = { withCredentials: true };
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const data = { study_id: datasetId, group_name: groupName, counter_id: counterId };
    const url = `${this.config.baseUrl}${this.familiesUrl}`;
    const response = this.http.post(url, data, options).pipe(map(res => res as Array<string>));
    return response;
  }

  public getTags(): Observable<object> {
    const options = { withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.tagsUrl}`, options);
  }
}
