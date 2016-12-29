import { Injectable } from '@angular/core';
import { Headers, Http, Response } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { Dataset } from './dataset';

@Injectable()
export class DatasetService {
  private datasetUrl = 'dataset';
  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http
  ) { }

  //  private handleError(error: any): Promise<any> {
  //    console.error('An error occured', error);
  //    return Promise.reject(error.message || error);
  //  }
  private handleError(error: any) {
    console.error('An error occured', error);
    return Observable.throw(error.message
      ? error.message
      : error.status
        ? `${error.status} - ${error.statusText}`
        : 'Server Error');
  }

  private parseDatasetsResponse(res: Response): Dataset[] {
    console.error(res.json());

    return res.json() as Dataset[];

  }

  getDatasets(): Observable<Dataset[]> {
    return this.http.get(this.datasetUrl)
      .map(this.parseDatasetsResponse)
      .catch(this.handleError);
  }

}
