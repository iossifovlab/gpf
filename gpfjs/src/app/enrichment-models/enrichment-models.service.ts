import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';

import { ConfigService } from '../config/config.service';
import { IdDescriptionName } from './iddescription';
import { map } from 'rxjs/operators';

export interface EnrichmentModels {
  countings: IdDescriptionName[];
  backgrounds: IdDescriptionName[];
  defaultBackground: string;
  defaultCounting: string;
}

@Injectable()
export class EnrichmentModelsService {
  private readonly enrichmentModelsUrl = 'enrichment/models';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getBackgroundModels(datasetId: string): Observable<EnrichmentModels> {
    const url = `${this.config.baseUrl}${this.enrichmentModelsUrl}/${datasetId}`;
    return this.http
      .get(url)
      .pipe(map((res: {
        counting: { id: string; name: string; desc: string } [];
        background: { id: string;name: string;desc: string } [];
        defaultBackground: string;
        defaultCounting: string;
      }) => ({
        countings: res['counting'].map(j => new IdDescriptionName(j.id, j.desc, j.name)),
        backgrounds: res['background'].map(j => new IdDescriptionName(j.id, j.desc, j.name)),
        defaultBackground: res['defaultBackground'],
        defaultCounting: res['defaultCounting']
      })));
  }
}
