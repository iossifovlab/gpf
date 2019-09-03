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
  private deleteQueryEndpoint = 'query_state/delete';

  private userSaveQueryEndpoint = 'user_queries/save';
  private userCollectQueriesEndpoint = 'user_queries/collect';

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
