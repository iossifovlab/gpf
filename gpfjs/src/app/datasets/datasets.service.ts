import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable, Scheduler } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';

import { Dataset } from '../datasets/datasets';
import { UsersService } from '../users/users.service';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';
import { Subject, ReplaySubject, BehaviorSubject } from 'rxjs';

@Injectable()
export class DatasetsService {
  private datasetUrl = 'datasets/';

  private headers = new Headers({ 'Content-Type': 'application/json' });
  private datasets$ = new ReplaySubject<Array<Dataset>>(1);
  private selectedDataset$ = new ReplaySubject<Dataset>(1);
  private _selectedDatasetId$ = new BehaviorSubject<string>(null);

  constructor(
    private http: Http,
    private config: ConfigService,
    private usersService: UsersService
  ) {
    this._selectedDatasetId$.asObservable()
      .switchMap(selectedDatasetId => {
        if (!selectedDatasetId) {
          return Observable.of(null);
        }

        return this.getDataset(selectedDatasetId);
      })
      .catch(errors => Observable.of(null))
      .filter(a => !!a)
      .subscribe(dataset => {
        this.selectedDataset$.next(dataset);
      });

    this.usersService.getUserInfoObservable()
      .map(user => user.email || '')
      .distinctUntilChanged()
      .subscribe(() => {
        this.reloadAllDatasets();
      });
  }

  getDatasets(): Observable<Dataset[]> {
    let options = new RequestOptions({ withCredentials: true });
    return this.http.get(this.datasetUrl, options)
      .map(res => {
        let datasets = Dataset.fromJsonArray(res.json().data);
        this.datasets$.next(datasets);
        return datasets;
      });
  }

  getDataset(datasetId: string): Observable<Dataset> {
    let url = `${this.datasetUrl}${datasetId}`;
    let options = new RequestOptions({ withCredentials: true });

    return this.http.get(url, options)
      .map(res => {
        return Dataset.fromJson(res.json().data);
      });
  }

  setSelectedDataset(dataset: Dataset): void {
    if (this._selectedDatasetId$.getValue() !== dataset.id) {
      this._selectedDatasetId$.next(dataset.id);
    }
  }

  setSelectedDatasetById(datasetId: string): void {
    if (this._selectedDatasetId$.getValue() !== datasetId) {
      this._selectedDatasetId$.next(datasetId);
    }
  }

  reloadSelectedDataset() {
    this._selectedDatasetId$.next(this._selectedDatasetId$.value);
  }

  getSelectedDataset() {
    return this.selectedDataset$.asObservable().subscribeOn(Scheduler.async);
  }

  getDatasetsObservable() {
    return this.datasets$.asObservable();
  }

  hasSelectedDataset() {
    return !!this._selectedDatasetId$.getValue();
  }

  private reloadAllDatasets() {
    this.getDatasets().take(1).subscribe(() => {});
  }
}
