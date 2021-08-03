import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { ContinuousMeasure, HistogramData } from './measures';
import { Partitions } from '../gene-weights/gene-weights';
import { map } from 'rxjs/operators';

@Injectable()
export class MeasuresService {
  private readonly continuousMeasuresUrl = 'measures/type/continuous';
  private readonly measureHistogramUrl = 'measures/histogram';
  private readonly measurePartitionsUrl = 'measures/partitions';
  private readonly regressionsUrl = 'measures/regressions';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getContinuousMeasures(datasetId: string): Observable<Array<ContinuousMeasure>> {
    const params = new HttpParams().set('datasetId', datasetId);
    const requestOptions = { withCredentials: true, params: params };

    return this.http
      .get(this.config.baseUrl + this.continuousMeasuresUrl, requestOptions)
      .pipe(map((res: any) => {
        return ContinuousMeasure.fromJsonArray(res);
      }));
  }

  getMeasureHistogram(datasetId: string, measureName: string) {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.measureHistogramUrl, { datasetId: datasetId, measure: measureName }, options)
      .pipe(map(res => {
        return HistogramData.fromJson(res);
      }));
  }

  getMeasurePartitions(datasetId: string, measureName: string, rangeStart: number, rangeEnd: number) {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.measurePartitionsUrl, {
        datasetId: datasetId,
        measure: measureName,
        min: rangeStart,
        max: rangeEnd
      }, options)
      .pipe(map(res => {
        return Partitions.fromJson(res);
      }));
  }

  getRegressions(datasetId: string) {
    const params = new HttpParams().set('datasetId', datasetId);
    const requestOptions = { withCredentials: true, params: params };

    return this.http.get(this.config.baseUrl + this.regressionsUrl, requestOptions);
  }
}
