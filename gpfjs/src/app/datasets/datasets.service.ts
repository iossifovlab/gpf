import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable, ReplaySubject, BehaviorSubject, asyncScheduler, of } from 'rxjs';

import { Dataset, DatasetDetails } from '../datasets/datasets';
import { UsersService } from '../users/users.service';
import { ConfigService } from '../config/config.service';
import { catchError, distinctUntilChanged, filter, map, mergeMap, subscribeOn, switchMap, take } from 'rxjs/operators';

@Injectable()
export class DatasetsService {
  private readonly datasetUrl = 'datasets';
  private readonly permissionDeniedPromptUrl = 'datasets/denied_prompt';
  private readonly datasetsDetailsUrl = 'datasets/details';
  private readonly datasetPedigreeUrl = 'datasets/pedigree';

  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });
  private datasets$ = new ReplaySubject<Array<Dataset>>(1);
  private selectedDataset$ = new ReplaySubject<Dataset>(1);
  private selectedDatasetId$ = new BehaviorSubject<string>(null);
  private selectedDatasetDetails$ = new BehaviorSubject<DatasetDetails>(null);

  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private usersService: UsersService
  ) {
    this.selectedDatasetId$.asObservable().pipe(
      switchMap(selectedDatasetId => {
        if (!selectedDatasetId) {
          return of(null);
        }

        return this.getDataset(selectedDatasetId);
      }),
      catchError(() => of(null)),
      filter(a => !!a),
      mergeMap((dataset: Dataset) => {
        this.selectedDataset$.next(dataset);
        return this.getDatasetDetails(dataset.id);
      })
    ).subscribe((datasetDetails: DatasetDetails) => {
      this.selectedDatasetDetails$.next(datasetDetails);
    });

    this.usersService.getUserInfoObservable().pipe(
      map(user => user.email || ''),
      distinctUntilChanged()
    ).subscribe(() => {
      this.reloadAllDatasets();
    });
  }

  getDatasets(): Observable<Dataset[]> {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.datasetUrl, options).pipe(
      map(res => {
        const datasets = Dataset.fromJsonArray(res['data']);
        this.datasets$.next(datasets);
        return datasets;
      })
    );
  }

  getDataset(datasetId: string): Observable<Dataset> {
    const url = `${this.datasetUrl}/${datasetId}`;
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + url, options).pipe(
      map(res => {
        return Dataset.fromJson(res['data']);
      })
    );
  }

  setSelectedDataset(dataset: Dataset): void {
    if (this.selectedDatasetId$.getValue() !== dataset.id) {
      this.selectedDatasetId$.next(dataset.id);
    }
  }

  setSelectedDatasetById(datasetId: string): void {
    if (this.selectedDatasetId$.getValue() !== datasetId) {
      this.selectedDatasetId$.next(datasetId);
    }
  }

  reloadSelectedDataset() {
    this.selectedDatasetId$.next(this.selectedDatasetId$.value);
  }

  getSelectedDataset() {
    return this.selectedDataset$.asObservable().pipe(
      subscribeOn(asyncScheduler)
    );
  }

  getSelectedDatasetId() {
    return this.selectedDatasetId$.value;
  }

  getDatasetsObservable() {
    return this.datasets$.asObservable();
  }

  hasSelectedDataset() {
    return !!this.selectedDatasetId$.getValue();
  }

  getSelectedDatasetDetails(): DatasetDetails {
    return this.selectedDatasetDetails$.getValue();
  }

  private reloadAllDatasets() {
    this.getDatasets().pipe(take(1)).subscribe(() => {});
  }

  getPermissionDeniedPrompt() {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.permissionDeniedPromptUrl, options).pipe(
      map(res => res['data'])
    );
  }

  getDatasetDetails(datasetId: string): Observable<DatasetDetails> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http.get(`${this.config.baseUrl}${this.datasetsDetailsUrl}/${datasetId}`, options).pipe(
      map(res => {
        return DatasetDetails.fromJson(res);
      })
    );
  }

  getDatasetPedigreeColumnDetails(datasetId: string, column: string): Observable<Object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.datasetPedigreeUrl}/${datasetId}/${column}`, options);
  }
}
