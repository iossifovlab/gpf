import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { CookieService } from 'ngx-cookie';

import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';
import { ConfigService } from '../config/config.service';

@Injectable()
export class PhenoBrowserService {
  private readonly instrumentsUrl = 'pheno_browser/instruments';
  private readonly measuresUrl = 'pheno_browser/measures';
  private readonly downloadUrl = 'pheno_browser/download';

  constructor(
    private http: HttpClient,
    private cookieService: CookieService,
    private config: ConfigService
  ) {}

  private getHeaders() {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };

    return headers;
  }

  getInstruments(datasetId: string): Observable<PhenoInstruments> {
    const headers = this.getHeaders();
    const searchParams = new HttpParams().set('dataset_id', datasetId);
    const options = {headers: headers, withCredentials: true, params: searchParams};

    return this.http
      .get(this.config.baseUrl + this.instrumentsUrl, options)
      .map(response => response as PhenoInstruments);
  }

  getMeasures(datasetId: string, instrument: PhenoInstrument, search: string): Observable<PhenoMeasures> {
    const headers = this.getHeaders();
    const searchParams = new HttpParams().set('dataset_id', datasetId).set('instrument', instrument).set('search', search);
    const options = {headers: headers, withCredentials: true, params: searchParams};

    return this.http
      .get(this.config.baseUrl + this.measuresUrl, options)
      .map(response => PhenoMeasures.fromJson(response))
      .map(PhenoMeasures.addBasePath);
  }

  getDownloadLink(instrument: PhenoInstrument, datasetId: string) {
    return `${this.config.baseUrl}${this.downloadUrl}`
           + `?dataset_id=${datasetId}&instrument=${instrument}`;
  }
}
