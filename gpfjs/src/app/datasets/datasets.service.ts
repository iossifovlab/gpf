import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';

import { Dataset } from '../datasets/datasets';
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
    private config: ConfigService
  ) {
    Observable
      .combineLatest(this.datasets$, this._selectedDatasetId$)
      .map(([datasets, selectedDatasetId]) => {
        if (!selectedDatasetId) {
          return null;
        }
        let selectedDataset = datasets.find(ds => ds.id === selectedDatasetId);

        if (!selectedDataset) {
          this._selectedDatasetId$.next('');
        }

        return selectedDataset;
      })
      .subscribe(dataset => {
        this.selectedDataset$.next(dataset);
      });
  }

  getDatasets(): Observable<Dataset[]> {
    let options = new RequestOptions({ withCredentials: true });
    return this.http
      .get(this.datasetUrl, options)
      .map(res => {
        let datasets = Dataset.fromJsonArray(res.json().data);
        this.datasets$.next(datasets);
        return datasets;
      });
  }

  getDataset(datasetId: string): Observable<Dataset> {
    let url = `${this.datasetUrl}${datasetId}`;

    return this.http
      .get(url)
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

  getSelectedDataset() {
    return this.selectedDataset$.asObservable();
  }

  getDatasetsObservable() {
    return this.datasets$.asObservable();
  }

  hasSelectedDataset() {
    return !!this._selectedDatasetId$.getValue();
  }
}
