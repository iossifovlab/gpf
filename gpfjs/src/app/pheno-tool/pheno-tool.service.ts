import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { PhenoToolResults } from './pheno-tool-results';
import { map } from 'rxjs/operators';

@Injectable()
export class PhenoToolService {
  private readonly phenoToolUrl = 'pheno_tool';
  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getPhenoToolResults(filter): Observable<any> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.phenoToolUrl, filter, options)
      .pipe(map(res => {
        return PhenoToolResults.fromJson(res);
      }));
  }
}
