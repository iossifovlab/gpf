import { Injectable } from '@angular/core';
import { Headers, Http, Response } from '@angular/http';
import { Observable } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';

import { Phenotype } from '../phenotypes/phenotype';
import { Dataset } from '../dataset/dataset';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

@Injectable()
export class DatasetService {
  private datasetUrl = 'dataset';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  selectedDatasetId: string = 'SD';
  private cachedDatasets: Dataset[];

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getDatasets(): Observable<Dataset[]> {
    console.log('getting datsets from: ', this.datasetUrl);
    return this.http
      .get(this.datasetUrl)
      .map(res => {
        return Dataset.fromJsonArray(res.json().data);
      });
  }

  getDataset(datasetId: string): Observable<Dataset> {
    let url = `${this.datasetUrl}/${datasetId}`;
    console.log('getting a dataset from: ', url);

    return this.http
      .get(url)
      .map(res => {
        console.log('datasets response: ', res);
        return Dataset.fromJson(res.json().data);
      });
  }

}
