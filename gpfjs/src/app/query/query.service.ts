import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';



import { ConfigService } from '../config/config.service';
import { GenotypePreviewsArray } from '../genotype-preview-model/genotype-preview';
import { QueryData } from './query';
import { Router } from '@angular/router';
import { Location } from '@angular/common';



@Injectable()
export class QueryService {
  private genotypePreviewUrl = 'genotype_browser/preview';
  private saveQueryEndpoint = 'query_state/save';
  private loadQueryEndpoint = 'query_state/load';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private location: Location,
    private router: Router,
    private http: Http,
    private config: ConfigService
  ) {
  }

  private parseGenotypePreviewResponse(response: Response): GenotypePreviewsArray {
    const data = response.json();
    const genotypePreviewsArray = GenotypePreviewsArray.fromJson(data);
    return genotypePreviewsArray;
  }

  getGenotypePreviewByFilter(filter: QueryData): Observable<GenotypePreviewsArray> {
    const options = new RequestOptions({
      headers: this.headers, withCredentials: true
    });

    return this.http.post(this.genotypePreviewUrl, filter, options)
      .map(this.parseGenotypePreviewResponse);
  }

  saveQuery(queryData: {}, page: string) {
    const options = new RequestOptions({
        headers: this.headers
    });
    const data = {
        data: queryData,
        page: page
    };

    return this.http
        .post(this.saveQueryEndpoint, data, options)
        .map(response => response.json());

  }

  loadQuery(uuid: string) {
    const options = new RequestOptions({
        headers: this.headers,
        withCredentials: true
    });

    return this.http
        .post(this.loadQueryEndpoint, { uuid: uuid }, options)
        .map(response => response.json());

  }

  getLoadUrl(uuid: string) {
    let pathname = this.router.createUrlTree(
      ['load-query', uuid]).toString();
    pathname = this.location.prepareExternalUrl(pathname);
    return window.location.origin + pathname;
  }

  getLoadUrlFromResponse(response: {}) {
    return this.getLoadUrl(response['uuid']);
  }
}
