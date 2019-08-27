import { Injectable } from '@angular/core';
import { Http, Headers, Response, URLSearchParams, RequestOptions } from '@angular/http';

// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';

import { ConfigService } from '../config/config.service';

@Injectable()
export class PhenoBrowserService {

  private instrumentsUrl = 'pheno_browser/instruments';
  private measuresUrl = 'pheno_browser/measures';
  private downloadUrl = 'pheno_browser/download';

  constructor(
    private http: Http,
    private config: ConfigService
  ) {}

  private getOptions(): RequestOptions {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = new Headers({ 'X-CSRFToken': csrfToken });
    const options = new RequestOptions({ headers: headers, withCredentials: true });

    return options;
  }

  getInstruments(datasetId: string): Observable<PhenoInstruments> {

    const options = this.getOptions();
    options.search = new URLSearchParams();

    options.search.set('dataset_id', datasetId);

    return this.http
      .get(this.instrumentsUrl, options)
      .map((response: Response) => response.json() as PhenoInstruments);
  }

  getMeasures(datasetId: string, instrument: PhenoInstrument, search: string): Observable<PhenoMeasures> {

    const options = this.getOptions();
    options.search = new URLSearchParams();

    options.search.set('dataset_id', datasetId);
    options.search.set('instrument', instrument);
    options.search.set('search', search);

    return this.http
      .get(this.measuresUrl, options)
      .map((response) => PhenoMeasures.fromJson(response.json()))
      .map(PhenoMeasures.addBasePath);
  }

  getDownloadLink(instrument: PhenoInstrument, datasetId: string) {
    return `${this.config.baseUrl}${this.downloadUrl}`
           + `?dataset_id=${datasetId}&instrument=${instrument}`;
  }
}
