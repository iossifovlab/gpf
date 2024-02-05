import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams, HttpResponse } from '@angular/common/http';
import { Observable, Subject, of } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures, PhenoMeasure } from './pheno-browser';
import { ConfigService } from '../config/config.service';
import { catchError, map } from 'rxjs/operators';
import { AuthService } from 'app/auth.service';

const oboe = require('oboe');

@Injectable()
export class PhenoBrowserService {
  private readonly instrumentsUrl = 'pheno_browser/instruments';
  private readonly measuresUrl = 'pheno_browser/measures';
  private readonly measuresInfoUrl = 'pheno_browser/measures_info';
  private readonly downloadUrl = 'pheno_browser/download';
  private readonly measureDescription = 'pheno_browser/measure_description';

  public measuresStreamingFinishedSubject = new Subject();

  public constructor(
    private http: HttpClient,
    private cookieService: CookieService,
    private config: ConfigService,
    private authService: AuthService
  ) {}

  public getMeasureDescription(datasetId: string, measureId: string): Observable<object> {
    const headers = this.getHeaders();
    const searchParams = new HttpParams().set('dataset_id', datasetId).set('measure_id', measureId);
    const options = { headers: headers, withCredentials: true, params: searchParams };
    return this.http.get(this.config.baseUrl + this.measureDescription, options).pipe(map(res => res));
  }

  private getHeaders() {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' };

    return headers;
  }

  public getInstruments(datasetId: string): Observable<PhenoInstruments> {
    const headers = this.getHeaders();
    const searchParams = new HttpParams().set('dataset_id', datasetId);
    const options = {headers: headers, withCredentials: true, params: searchParams};

    return this.http
      .get(this.config.baseUrl + this.instrumentsUrl, options)
      .pipe(map(response => response as PhenoInstruments));
  }

  public getMeasures(datasetId: string, instrument: PhenoInstrument, search: string): Observable<PhenoMeasure> {
    const headers = this.getHeaders();
    const searchParams =
      new HttpParams()
        .set('dataset_id', datasetId)
        .set('instrument', instrument)
        .set('search', search);
    const measuresSubject: Subject<PhenoMeasure> = new Subject();

    if (this.authService.accessToken !== '') {
      headers['Authorization'] = `Bearer ${this.authService.accessToken}`;
    }

    oboe({
      url: `${this.config.baseUrl}${this.measuresUrl}?${searchParams.toString()}`,
      method: 'GET',
      headers: headers,
      withCredentials: true,
    }).start(data => {
      this.measuresStreamingFinishedSubject.next(false);
    }).node('!.*', data => {
      measuresSubject.next(data);
    }).done(data => {
      if (data.length === 0) {
        measuresSubject.next(null);
      }
      this.measuresStreamingFinishedSubject.next(true);
    }).fail(error => {
      this.measuresStreamingFinishedSubject.next(true);
      console.warn('oboejs encountered a fail event while streaming');
    });

    return measuresSubject.pipe(map(data => {
      if (data === null) {
        return null;
      }
      return PhenoMeasure.fromJson(data['measure'] as object);
    }));
  }

  public getMeasuresInfo(datasetId: string): Observable<PhenoMeasures> {
    const headers = this.getHeaders();
    const searchParams = new HttpParams().set('dataset_id', datasetId);
    const options = {headers: headers, withCredentials: true, params: searchParams};

    return this.http
      .get(this.config.baseUrl + this.measuresInfoUrl, options)
      .pipe(map(response => PhenoMeasures.fromJson(response)));
  }

  public getDownloadLink(instrument: PhenoInstrument, datasetId: string): string {
    return `${this.config.baseUrl}${this.downloadUrl}`
           + `?dataset_id=${datasetId}&instrument=${instrument}`;
  }

  public validateMeasureDownload(data: {
    /* eslint-disable @typescript-eslint/naming-convention */
    dataset_id: string;
    instrument: string;
    search_term: string;
    /* eslint-enable */
  }): Observable<HttpResponse<object>> {
    const headers = this.getHeaders();
    const params =
      new HttpParams()
        .set('dataset_id', data.dataset_id)
        .set('instrument', data.instrument)
        .set('search_term', data.search_term);

    return this.http
      .head<HttpResponse<object>>(
        this.config.baseUrl + 'pheno_browser/download',
        {headers: headers, withCredentials: true, params: params, observe: 'response'}
      ).pipe(
        catchError((err: HttpResponse<object>) => of(err))
      );
  }

  public getDownloadMeasuresLink(data: {
    /* eslint-disable @typescript-eslint/naming-convention */
    dataset_id: string;
    instrument: string;
    search_term: string;
     /* eslint-enable */
  }): string {
    return this.config.baseUrl
      + 'pheno_browser/download?'
      + `dataset_id=${data.dataset_id}`
      + `&instrument=${data.instrument}`
      + `&search_term=${data.search_term}`;
  }
}
