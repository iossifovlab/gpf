import { Injectable } from '@angular/core';
import { Headers, Http, Response } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';

import { Phenotype } from '../phenotypes/phenotype';
import { Dataset } from '../dataset/dataset';
import { ConfigService } from '../config/config.service';


@Injectable()
export class DatasetService {
  private datasetUrl = 'dataset';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  selectedDatasetId: string = 'SD';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getDatasets(): Observable<IdName[]> {
    return Observable.from([]);
  }

  getDataset(datasetId: string): Observable<Dataset> {
    return Observable.create(null);
  }
}
