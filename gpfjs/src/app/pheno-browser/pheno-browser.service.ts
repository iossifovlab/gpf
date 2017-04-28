import { Injectable } from '@angular/core';
import { Http, Headers, Response, URLSearchParams, RequestOptions, RequestOptionsArgs } from '@angular/http';

import { Observable } from 'rxjs';
import { CookieService } from 'ngx-cookie';

import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';

@Injectable()
export class PhenoBrowserService {

  private instrumentsUrl = 'pheno_browser/instruments';
  private measuresUrl = 'pheno_browser/measures';

  constructor(
    private http: Http,
    private cookieService: CookieService
  ) {}

  private getOptions(): RequestOptions {
    let csrfToken = this.cookieService.get("csrftoken");
    let headers = new Headers({ 'X-CSRFToken': csrfToken });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return options;
  }

  getInstruments(datasetId: string): Observable<PhenoInstruments> {

    let options = this.getOptions();
    options.search = new URLSearchParams();

    options.search.set('dataset_id', datasetId);

    return this.http
      .get(this.instrumentsUrl, options)
      .map((response: Response) => response.json() as PhenoInstruments);
  }

  getMeasures(datasetId: string, instrument: PhenoInstrument): Observable<PhenoMeasures> {

    let options = this.getOptions();
    options.search = new URLSearchParams();

    options.search.set('dataset_id', datasetId);
    options.search.set('measure', instrument);

    return this.http
      .get(this.measuresUrl, options)
      .map((response) => {
        let result = PhenoMeasures.fromJson(response.json());
        console.log(result);
        return result
      })
      .map(PhenoMeasures.addBasePath);
  }
}
