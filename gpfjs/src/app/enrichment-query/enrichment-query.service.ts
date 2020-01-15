import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentResults } from './enrichment-result';

@Injectable()
export class EnrichmentQueryService {
  private readonly genotypePreviewUrl = 'enrichment/test';
  private  headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getEnrichmentTest(filter): Observable<EnrichmentResults> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.genotypePreviewUrl, filter, options)
      .map(res => {
        return EnrichmentResults.fromJson(res);
      });
  }
}
