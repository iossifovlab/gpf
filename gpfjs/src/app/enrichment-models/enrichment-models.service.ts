import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentModels } from './enrichment-models';



@Injectable()
export class EnrichmentModelsService {
  private enrichmentModelsUrl = 'enrichment/models/';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getBackgroundModels(): Observable<EnrichmentModels> {
    return this.http
      .get(this.enrichmentModelsUrl)
      .map(res => {
        return EnrichmentModels.fromJson(res.json());
      });
  }
}
