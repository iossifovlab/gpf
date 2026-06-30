import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentResults } from './enrichment-result';
import { map } from 'rxjs/operators';

@Injectable()
export class EnrichmentQueryService {
  private http = inject(HttpClient);
  private config = inject(ConfigService);

  private readonly genotypePreviewUrl = 'enrichment/test';
  // eslint-disable-next-line @typescript-eslint/naming-convention
  private headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  public getEnrichmentTest(filter: object): Observable<EnrichmentResults> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.genotypePreviewUrl, filter, options)
      .pipe(map(res => EnrichmentResults.fromJson(res)));
  }
}
