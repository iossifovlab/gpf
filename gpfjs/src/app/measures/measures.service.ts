import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { ContinuousMeasure, HistogramData, Measure, MeasureHistogram } from './measures';
import { Partitions } from '../gene-scores/gene-scores';
import { map } from 'rxjs/operators';

@Injectable()
export class MeasuresService {
  private readonly measuresListUrl = 'measures/list';
  private readonly measureRolesUrl = 'measures/role-list';
  private readonly continuousMeasuresUrl = 'measures/type/continuous';
  private readonly measureHistogramUrl = 'measures/histogram';
  private readonly measureHistogramUrlBeta = 'measures/histogram-beta';
  private readonly measurePartitionsUrl = 'measures/partitions';
  private readonly regressionsUrl = 'measures/regressions';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getMeasureRoles(datasetId: string): Observable<string[]> {
    return this.http
      .post(this.config.baseUrl + this.measureRolesUrl,
        { datasetId: datasetId }
      )
      .pipe(map(res => res as string[]));
  }

  public getMeasureList(datasetId: string): Observable<Array<Measure>> {
    const params = new HttpParams().set('datasetId', datasetId);
    const requestOptions = { withCredentials: true, params: params };

    return this.http
      .get(this.config.baseUrl + this.measuresListUrl, requestOptions)
      .pipe(map((res: object[]) => Measure.fromJsonArray(res)));
  }

  public getContinuousMeasures(datasetId: string): Observable<Array<ContinuousMeasure>> {
    const params = new HttpParams().set('datasetId', datasetId);
    const requestOptions = { withCredentials: true, params: params };

    return this.http
      .get(this.config.baseUrl + this.continuousMeasuresUrl, requestOptions)
      .pipe(map((res: object[]) => ContinuousMeasure.fromJsonArray(res)));
  }

  public getMeasureHistogram(datasetId: string, measureName: string): Observable<HistogramData> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post(
        this.config.baseUrl + this.measureHistogramUrl,
        { datasetId: datasetId, measure: measureName },
        options
      )
      .pipe(
        map((res) => HistogramData.fromJson(res))
      );
  }

  public getMeasureHistogramBeta(
    datasetId: string,
    measureName: string,
    roles?: string[]
  ): Observable<MeasureHistogram> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post(
        this.config.baseUrl + this.measureHistogramUrlBeta,
        { datasetId: datasetId, measure: measureName, roles: roles },
        options
      )
      .pipe(
        map((res) => MeasureHistogram.fromJson(res))
      );
  }

  public getMeasurePartitions(
    datasetId: string,
    measureName: string,
    rangeStart: number,
    rangeEnd: number
  ): Observable<Partitions> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(
      this.config.baseUrl + this.measurePartitionsUrl,
      { datasetId: datasetId, measure: measureName, min: rangeStart, max: rangeEnd },
      options
    ).pipe(
      map((res) => Partitions.fromJson(res))
    );
  }

  public getRegressions(datasetId: string): Observable<object> {
    const params = new HttpParams().set('datasetId', datasetId);
    const requestOptions = { withCredentials: true, params: params };

    return this.http.get(
      this.config.baseUrl + this.regressionsUrl,
      requestOptions
    );
  }
}
