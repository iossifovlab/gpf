import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { ConfigService } from '../config/config.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';
import { EnrichmentQueryData } from './enrichment-query';


@Injectable()
export class EnrichmentQueryService {
  private genotypePreviewUrl = 'enrichment/test';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http,
    private config: ConfigService
  ) {

  }

  getEnrichmentTest(filter: EnrichmentQueryData): Observable<any> {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.genotypePreviewUrl, filter, options)
      .map(res => {
        return null;
      });
  }
}
