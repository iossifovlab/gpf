import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable, ReplaySubject, BehaviorSubject, zip, Subject } from 'rxjs';

import { Dataset } from '../datasets/datasets';
import { UsersService } from '../users/users.service';
import { ConfigService } from '../config/config.service';
import { distinctUntilChanged, map, take } from 'rxjs/operators';

@Injectable()
export class DatasetsService {
  private readonly datasetUrl = 'datasets';
  private readonly permissionDeniedPromptUrl = 'datasets/denied_prompt';
  private readonly datasetsDetailsUrl = 'datasets/details';
  private readonly datasetPedigreeUrl = 'datasets/pedigree';

  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });
  private datasets$ = new ReplaySubject<Array<Dataset>>(1);
  private selectedDataset$ = new BehaviorSubject<Dataset>(null);
  private datasetLoaded$ = new Subject<void>();
  private _hasLoadedAnyDataset = false;

  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private usersService: UsersService
  ) {
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
    const options = { headers: this.headers, withCredentials: true };

    const dataset$ = this.http.get(this.config.baseUrl + url, options);
    const details$ = this.http.get(`${this.config.baseUrl}${this.datasetsDetailsUrl}/${datasetId}`, options);

    return zip(dataset$, details$).pipe(map(datasetPack => Dataset.fromDatasetAndDetailsJson(datasetPack[0]['data'], datasetPack[1])));
  }

  setSelectedDataset(dataset: Dataset): void {
    this.setSelectedDatasetById(dataset.id);
  }

  setSelectedDatasetById(datasetId: string): void {
    if (this.selectedDataset$.getValue()?.id === datasetId) {
      return;
    }

    this.selectedDataset$.next(null);

    this.getDataset(datasetId).pipe(take(1)).subscribe(dataset => {
      this.selectedDataset$.next(dataset);
      this._hasLoadedAnyDataset = true;
      this.datasetLoaded$.next();
    });
  }

  reloadSelectedDataset() {
    this.datasetLoaded$.next();
  }

  getSelectedDatasetObservable(): Observable<Dataset> {
    return this.selectedDataset$.asObservable();
  }

  getSelectedDataset(): Dataset {
    return this.selectedDataset$.getValue();
  }

  getSelectedDatasetId() {
    return this.selectedDataset$.getValue().id;
  }

  getDatasetsObservable() {
    return this.datasets$.asObservable();
  }

  getDatasetsLoadedObservable() {
    return this.datasetLoaded$;
  }

  hasSelectedDataset() {
    return !!this.selectedDataset$.getValue();
  }

  hasLoadedAnyDataset() {
    return this._hasLoadedAnyDataset;
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

  getDatasetPedigreeColumnDetails(datasetId: string, column: string): Observable<Object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.datasetPedigreeUrl}/${datasetId}/${column}`, options);
  }
}
