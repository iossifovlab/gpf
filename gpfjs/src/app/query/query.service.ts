import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
// tslint:disable-next-line:import-blacklist
import { Observable, Subject } from 'rxjs';

const oboe = require('oboe');

import { environment } from 'environments/environment';

import { QueryData } from './query';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewInfo, GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';


@Injectable()
export class QueryService {
  private genotypePreviewVariantsUrl = 'genotype_browser/preview/variants';
  private saveQueryEndpoint = 'query_state/save';
  private loadQueryEndpoint = 'query_state/load';
  private deleteQueryEndpoint = 'query_state/delete';

  private userSaveQueryEndpoint = 'user_queries/save';
  private userCollectQueriesEndpoint = 'user_queries/collect';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  private connectionEstablished = false;
  private oboeInstance = null;
  public streamingFinishedSubject = new Subject(); // This is for notifying that the streaming has completely finished

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

    return this.http.post(this.genotypePreviewVariantsUrl, filter, options)
      .map(this.parseGenotypePreviewInfoResponse);
  }

  streamPost(url: string, filter: QueryData) {
    if (this.connectionEstablished) {
      this.oboeInstance.abort();
    }

    const streamingSubject = new Subject();
    this.oboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: this.headers.toJSON(),
      body: filter,
      withCredentials: true
    }).start(data => {
      this.connectionEstablished = true;
    }).node('!.*', data => {
      streamingSubject.next(data);
    }).done(data => {
      this.streamingFinishedSubject.next(true);
      streamingSubject.next(null); // Emit null so the loading service can stop the loading overlay even if no variants were received
    }).fail(error => {
      this.connectionEstablished = false;
      this.streamingFinishedSubject.next(true);
      console.warn('oboejs encountered a fail event while streaming');
      streamingSubject.next(null);
    });
    return streamingSubject;
  }

  getGenotypePreviewVariantsByFilter(filter: QueryData, genotypePreviewInfo: GenotypePreviewInfo,
    loadingService: any): GenotypePreviewVariantsArray {
    const genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();

    this.streamPost(this.genotypePreviewVariantsUrl, filter).subscribe(variant => {
      this.parseGenotypePreviewVariantsResponse(variant, genotypePreviewInfo, genotypePreviewVariantsArray);
      loadingService.setLoadingStop(); // Stop the loading overlay when at least one variant has been loaded
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

  deleteQuery(uuid:string) {
    const options = new RequestOptions({
        headers: this.headers,
        withCredentials: true
    });

    return this.http.post(this.deleteQueryEndpoint, { uuid: uuid }, options)
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

  saveUserQuery(uuid: string, query_name: string, query_description: string) {
    const options = new RequestOptions({
      headers: this.headers, withCredentials: true
    });

    const data = {
      query_uuid: uuid,
      name: query_name,
      description: query_description
    };

    return this.http
      .post(this.userSaveQueryEndpoint, data, options);
  }

  collectUserSavedQueries() {
    const options = new RequestOptions({withCredentials: true});
    return this.http
      .get(this.userCollectQueriesEndpoint, options)
      .map(response => response.json());
  }
}
