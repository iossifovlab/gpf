import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentResults } from './enrichment-result';
import { map } from 'rxjs/operators';

@Injectable()
export class EnrichmentQueryService {
  private readonly genotypePreviewUrl = 'enrichment/test';
  private  headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getEnrichmentTest(filter: object): Observable<EnrichmentResults> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.genotypePreviewUrl, filter, options)
      .pipe(map(res => {
        return EnrichmentResults.fromJson(res);
      }));
  }
}
