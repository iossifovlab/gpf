import { Injectable } from '@angular/core';
import { Headers, Http, RequestOptions } from '@angular/http';
// tslint:disable-next-line:import-blacklist
import { Observable, ReplaySubject, BehaviorSubject } from 'rxjs';
import { Scheduler } from 'rxjs-compat';

import { Dataset, DatasetDetails } from '../datasets/datasets';
import { UsersService } from '../users/users.service';
import { ConfigService } from '../config/config.service';

@Injectable()
export class DatasetsService {
  private readonly datasetUrl = 'datasets';
  private readonly permissionDeniedPromptUrl = 'datasets/denied_prompt';
  private readonly datasetsDetailsUrl = 'datasets/details'

  private readonly headers = new Headers({ 'Content-Type': 'application/json' });
  private datasets$ = new ReplaySubject<Array<Dataset>>(1);
  private selectedDataset$ = new ReplaySubject<Dataset>(1);
  private selectedDatasetId$ = new BehaviorSubject<string>(null);
  private selectedDatasetDetails$ = new BehaviorSubject<DatasetDetails>(null);

  constructor(
    private http: Http,
    private config: ConfigService,
    private usersService: UsersService
  ) {
    this.selectedDatasetId$.asObservable()
      .switchMap(selectedDatasetId => {
        if (!selectedDatasetId) {
          return Observable.of(null);
        }

        return this.getDataset(selectedDatasetId);
      })
      .catch(errors => Observable.of(null))
      .filter(a => !!a)
      .mergeMap((dataset: Dataset) => {
        this.selectedDataset$.next(dataset);
        return this.getDatasetDetails(dataset.id);
      })
      .subscribe((datasetDetails: DatasetDetails) => {
        this.selectedDatasetDetails$.next(datasetDetails);
      });

    this.usersService.getUserInfoObservable()
      .map(user => user.email || '')
      .distinctUntilChanged()
      .subscribe(() => {
        this.reloadAllDatasets();
      });
  }

  getDatasets(): Observable<Dataset[]> {
    const options = new RequestOptions({ withCredentials: true });
    return this.http.get(this.datasetUrl, options)
      .map(res => {
        const datasets = Dataset.fromJsonArray(res.json().data);
        this.datasets$.next(datasets);
        return datasets;
      });
  }

  getDataset(datasetId: string): Observable<Dataset> {
    const url = `${this.datasetUrl}/${datasetId}`;
    const options = new RequestOptions({ withCredentials: true });

    return this.http.get(url, options)
      .map(res => {
        return Dataset.fromJson(res.json().data);
      });
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
    return this.selectedDataset$.asObservable().subscribeOn(Scheduler.async);
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
    this.getDatasets().take(1).subscribe(() => {});
  }

  getPermissionDeniedPrompt() {
    const options = new RequestOptions({ withCredentials: true });

    return this.http.get(this.permissionDeniedPromptUrl, options)
      .map(res => res.json().data);
  }

  getDatasetDetails(datasetId: string): Observable<DatasetDetails> {
    const options = new RequestOptions({ headers: this.headers, withCredentials: true });
    return this.http
      .get(`${this.datasetsDetailsUrl}/${datasetId}`, options)
      .map(res => {
        return DatasetDetails.fromJson(res.json())
      });
  }
}
