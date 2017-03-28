import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';

import {
  Dataset, DatasetsState,
  DATASETS_INIT, DATASETS_SELECT
} from '../datasets/datasets';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';
import { Subject, BehaviorSubject } from 'rxjs';
import { Store } from '@ngrx/store';

@Injectable()
export class DatasetsService {
  private datasetUrl = 'datasets/';

  private headers = new Headers({ 'Content-Type': 'application/json' });
  datasetsStore: Observable<DatasetsState>;

  constructor(
    private http: Http,
    private config: ConfigService,
    private store: Store<any>
  ) {

    this.datasetsStore = store.select('datasets');
  }

  getDatasets(): Observable<Dataset[]> {
    let options = new RequestOptions({ withCredentials: true });
    console.log('getting datsets from: ', this.datasetUrl);
    return this.http
      .get(this.datasetUrl, options)
      .map(res => {
        let datasets = Dataset.fromJsonArray(res.json().data);
        this.store.dispatch({
          'type': DATASETS_INIT,
          'payload': datasets
        });
        return datasets;
      });
  }

  getDataset(datasetId: string): Observable<Dataset> {
    let url = `${this.datasetUrl}${datasetId}`;
    console.log('getting a dataset from: ', url);

    return this.http
      .get(url)
      .map(res => {
        console.log('datasets response: ', res);
        return Dataset.fromJson(res.json().data);
      });
  }

  setSelectedDataset(dataset: Dataset): void {
    this.store.dispatch({
      'type': DATASETS_SELECT,
      'payload': dataset

    });
    // this.selectedDataset.next(dataset);
  }
}
