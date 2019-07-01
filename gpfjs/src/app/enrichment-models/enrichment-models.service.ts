import { Injectable } from '@angular/core';
import { Http } from '@angular/http';
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentModels } from './enrichment-models';



@Injectable()
export class EnrichmentModelsService {
  private enrichmentModelsUrl = 'enrichment/models';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getBackgroundModels(datasetId: String): Observable<EnrichmentModels> {
    const url = `${this.enrichmentModelsUrl}/${datasetId}`;

    return this.http
      .get(url)
      .map(res => {
        return EnrichmentModels.fromJson(res.json());
      });
  }
}
