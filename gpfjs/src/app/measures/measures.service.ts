import { Injectable } from '@angular/core';
import { Http, RequestOptions, URLSearchParams, Headers } from '@angular/http';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { ContinuousMeasure, HistogramData } from './measures'

@Injectable()
export class MeasuresService {
  private continuousMeasuresUrl = 'measures/type/continuous';
  private measureHistogramUrl = 'measures/histogram';

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

  getMeasureHistogram(datasetId: string, measureName: string) {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers });
    return this.http
      .post(this.measureHistogramUrl, { datasetId: datasetId, measure: measureName }, options)
      .map(res => {
        return HistogramData.fromJson(res.json());
      });
  }
}
