import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';



import { ConfigService } from '../config/config.service';
import { PhenoToolResults } from './pheno-tool-results';

@Injectable()
export class PhenoToolService {
  private phenoToolUrl = 'pheno_tool';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http,
    private config: ConfigService
  ) {

  }

  getPhenoToolResults(filter): Observable<any> {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.phenoToolUrl, filter, options)
      .map(res => {
        return PhenoToolResults.fromJson(res.json());;
      });
  }
}
