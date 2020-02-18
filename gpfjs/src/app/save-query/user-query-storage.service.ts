import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';

@Injectable()
export class UserQueryStorageService {
  private storeQueryEndpoint = 'user_queries/store';
  private retrieveQueryEndpoint = 'user_queries/retrieve';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http
  ) {}

  storeQuery(uuid: string, query_name: string, query_description: string) {
    const options = new RequestOptions({
      headers: this.headers, withCredentials: true
    });

    const data = {
      query_uuid: uuid,
      name: query_name,
      description: query_description
    };

    return this.http
      .post(this.storeQueryEndpoint, data, options);
  }

  retrieveQueries() {
    const options = new RequestOptions({withCredentials: true});
    return this.http
      .get(this.retrieveQueryEndpoint, options)
      .map(response => response.json());
  }
}
