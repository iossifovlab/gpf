import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { IdDescription } from 'app/common/iddescription';

export interface EnrichmentModels {
  countings: IdDescription[];
  backgrounds: IdDescription[];
}

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
        return {
          countings: res['counting'].map((j) => new IdDescription(j.name, j.desc)),
          backgrounds: res['background'].map((j) => new IdDescription(j.name, j.desc)),
        }
      });
  }
}
