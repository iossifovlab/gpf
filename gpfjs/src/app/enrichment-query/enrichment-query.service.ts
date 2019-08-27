import { Injectable } from '@angular/core';
import { Headers, Http, RequestOptions } from '@angular/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentResults } from './enrichment-result';

@Injectable()
export class EnrichmentQueryService {
  private genotypePreviewUrl = 'enrichment/test';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http,
    private config: ConfigService
  ) {

  }

  getEnrichmentTest(filter): Observable<EnrichmentResults> {
    const headers = new Headers({ 'Content-Type': 'application/json' });
    const options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.genotypePreviewUrl, filter, options)
      .map(res => {
        return EnrichmentResults.fromJson(res.json());
      });
  }
}
