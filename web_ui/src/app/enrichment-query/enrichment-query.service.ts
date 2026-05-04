import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentResults } from './enrichment-result';
import { map } from 'rxjs/operators';

@Injectable()
export class EnrichmentQueryService {
  private readonly genotypePreviewUrl = 'enrichment/test';
  // eslint-disable-next-line @typescript-eslint/naming-convention
  private headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getEnrichmentTest(filter: object): Observable<EnrichmentResults> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.genotypePreviewUrl, filter, options)
      .pipe(map(res => EnrichmentResults.fromJson(res)));
  }
}
