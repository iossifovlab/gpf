import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';


@Injectable()
export class SaveQueryService {
  private saveQueryEndpoint = 'query_state/save';
  private loadQueryEndpoint = 'query_state/load';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
      private http: Http
  ) {}

  saveQuery(queryData: {}, page: string) {
    let options = new RequestOptions({
        headers: this.headers
    });
    let data = {
        data: queryData,
        page: page
    };
    
    return this.http
        .post(this.saveQueryEndpoint, data, options)
        .map(response => response.json());

  }

  loadQuery(uuid: string) {
    let options = new RequestOptions({
        headers: this.headers,
        withCredentials: true
    });
    
    return this.http
        .post(this.loadQueryEndpoint, { uuid: uuid }, options)
        .map(response => response.json());

  }

}