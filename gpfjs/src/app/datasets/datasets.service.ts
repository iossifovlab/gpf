import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, ReplaySubject, zip, of } from 'rxjs';

import { Dataset } from '../datasets/datasets';
import { UsersService } from '../users/users.service';
import { ConfigService } from '../config/config.service';
import { distinctUntilChanged, map, share, take } from 'rxjs/operators';
import { DatasetPermissions } from 'app/datasets-table/datasets-table';

@Injectable()
export class DatasetsService {
  private readonly datasetUrl = 'datasets';
  private readonly permissionDeniedPromptUrl = 'datasets/denied_prompt';
  private readonly datasetsDetailsUrl = 'datasets/details';
  private readonly datasetPedigreeUrl = 'datasets/pedigree';
  private readonly visibleDatasetsUrl = 'datasets/visible';
  private readonly descriptionUrl = 'datasets/description';

  // eslint-disable-next-line @typescript-eslint/naming-convention
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });
  private datasets$ = new ReplaySubject<Array<Dataset>>(1);
  public datasetsLoading = false;

  public static genomeVersion = '';

  public static descriptionCache = [];

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private usersService: UsersService
  ) {
    this.usersService.getUserInfoObservable().pipe(
      map(user => user['email'] as string || ''),
      distinctUntilChanged()
    ).subscribe(() => {
      this.reloadAllDatasets();
    });
  }

  public getDatasets(): Observable<Dataset[]> {
    const options = { withCredentials: true };
    this.datasetsLoading = true;

    return this.http.get(this.config.baseUrl + this.datasetUrl, options).pipe(
      map((res: {data: Array<object>}) => {
        const datasets = Dataset.fromJsonArray(res.data);
        this.datasets$.next(datasets);
        this.datasetsLoading = false;
        return datasets;
      })
    );
  }

  public getDataset(datasetId: string): Observable<Dataset> {
    const url = `${this.datasetUrl}/${datasetId}`;
    const options = { headers: this.headers, withCredentials: true };

    const dataset$ = this.http.get(this.config.baseUrl + url, options);
    const details$ = this.http.get(`${this.config.baseUrl}${this.datasetsDetailsUrl}/${datasetId}`, options);

    return zip(dataset$, details$).pipe(map(
      (datasetPack: [any, any]) => Dataset.fromDatasetAndDetailsJson(datasetPack[0]['data'], datasetPack[1]))
    );
  }

  public getManagementDatasets(page: number, searchTerm: string): Observable<DatasetPermissions[]> {
    let url = `${this.config.baseUrl}${this.datasetUrl}/permissions?page=${page}`;
    if (searchTerm) {
      const searchParams = new HttpParams().set('search', searchTerm);
      url += `&${searchParams.toString()}`;
    }

    return this.http.get(url).pipe(
      map((response) => {
        if (response === null) {
          return [] as DatasetPermissions[];
        }
        return (response as object[]).map(dataset => DatasetPermissions.fromJson(dataset));
      })
    );
  }

  public getManagementDataset(datasetId: string): Observable<DatasetPermissions> {
    const url = `${this.config.baseUrl}${this.datasetUrl}/permissions/${datasetId}`;

    return this.http.get(url).pipe(
      map((response: object) => DatasetPermissions.fromJson(response))
    );
  }

  public getDatasetsObservable(): Observable<Dataset[]> {
    return this.datasets$.asObservable();
  }

  private reloadAllDatasets(): void {
    this.getDatasets().pipe(take(1)).subscribe(() => null);
  }

  public getPermissionDeniedPrompt(): Observable<string> {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.permissionDeniedPromptUrl, options).pipe(
      map(res => res['data'] as string)
    );
  }

  public getDatasetPedigreeColumnDetails(datasetId: string, column: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.datasetPedigreeUrl}/${datasetId}/${column}`, options);
  }

  public writeDatasetDescription(datasetId: string, description: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.post(
      `${this.config.baseUrl}${this.datasetUrl}/description/${datasetId}`,
      {description: description},
      options
    );
  }

  public getVisibleDatasets(): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.visibleDatasetsUrl}`, options);
  }

  public getDatasetDescription(datasetId: string): Observable<object> {
    if (DatasetsService.descriptionCache.length !== 0) {
      return of(DatasetsService.descriptionCache.find(d => d['datasetId'] === datasetId) as object);
    }

    const options = { headers: this.headers, withCredentials: true };
    const description$ = this.http.get(
      `${this.config.baseUrl}${this.descriptionUrl}/${datasetId}`, options
    ).pipe(take(1), share());
    description$.subscribe(description => {
      DatasetsService.descriptionCache.push({datasetId: datasetId, description: description['description'] as string});
    });

    return description$;
  }
}
