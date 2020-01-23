import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { EnrichmentModels } from './enrichment-models';

@Injectable()
export class EnrichmentModelsService {
  private readonly enrichmentModelsUrl = 'enrichment/models';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getBackgroundModels(datasetId: String): Observable<EnrichmentModels> {
    const url = `${this.config.baseUrl}${this.enrichmentModelsUrl}/${datasetId}`;

    return this.http
      .get(url)
      .map(res => {
        return EnrichmentModels.fromJson(res);
      });
  }
}
