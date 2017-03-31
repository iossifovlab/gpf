import { Injectable } from '@angular/core';
import { Http, RequestOptions, URLSearchParams } from '@angular/http';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { ContinuousMeasure } from './measures'

@Injectable()
export class MeasuresService {
  private continuousMeasuresUrl = 'measures/type/continuous';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getContinuousMeasures(datasetId: string): Observable<Array<ContinuousMeasure>> {
    let params: URLSearchParams = new URLSearchParams();
    params.set('datasetId', datasetId);

    let requestOptions = new RequestOptions();
    requestOptions.search = params;

    return this.http
      .get(this.continuousMeasuresUrl, requestOptions)
      .map(res => {
        return ContinuousMeasure.fromJsonArray(res.json());
      });
  }
}
