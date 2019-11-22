import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

const oboe = require('oboe');

import { environment } from 'environments/environment';

import { QueryData } from './query';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewInfo, GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';


@Injectable()
export class QueryService {
  private genotypePreviewUrl = 'genotype_browser/preview';
  private genotypePreviewVariantsUrl = 'genotype_browser/preview/variants';
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

  private parseGenotypePreviewInfoResponse(response: Response): GenotypePreviewInfo {
    const data = response.json();
    const genotypePreviewInfoArray = GenotypePreviewInfo.fromJson(data);
    return genotypePreviewInfoArray;
  }

  private parseGenotypePreviewVariantsResponse(
    response: any, genotypePreviewInfo: GenotypePreviewInfo,
    genotypePreviewVariantsArray: GenotypePreviewVariantsArray) {

    genotypePreviewVariantsArray.addPreviewVariant(response, genotypePreviewInfo);
  }

  getGenotypePreviewInfo(filter: QueryData): Observable<GenotypePreviewInfo> {
    const options = new RequestOptions({
      headers: this.headers, withCredentials: true
    });

    return this.http.post(this.genotypePreviewUrl, filter, options)
      .map(this.parseGenotypePreviewInfoResponse);
  }

  streamPost(url: string, filter: QueryData) {
    return new Observable(obs => {
      oboe({
        url: `${environment.apiPath}${url}`,
        method: 'POST',
        headers: this.headers.toJSON(),
        body: filter,
        withCredentials: true
      }).done(data => obs.next(data));
    });
  }

  getGenotypePreviewVariantsByFilter(filter: QueryData, genotypePreviewInfo: GenotypePreviewInfo): GenotypePreviewVariantsArray {
    const genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();

    this.streamPost(this.genotypePreviewVariantsUrl, filter).subscribe(variant => {
      this.parseGenotypePreviewVariantsResponse(variant, genotypePreviewInfo, genotypePreviewVariantsArray);
    });

    return genotypePreviewVariantsArray;
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
