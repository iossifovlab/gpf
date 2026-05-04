import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ConfigService } from '../config/config.service';
import { PhenoToolResults } from './pheno-tool-results';
import { map } from 'rxjs/operators';

@Injectable()
export class PhenoToolService {
  private readonly phenoToolUrl = 'pheno_tool';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getPhenoToolResults(filter: object): Observable<PhenoToolResults> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.phenoToolUrl, filter, options)
      .pipe(map(res => PhenoToolResults.fromJson(res)));
  }
}
