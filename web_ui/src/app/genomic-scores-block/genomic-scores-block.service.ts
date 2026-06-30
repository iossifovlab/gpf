import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';

import { GenomicScore } from './genomic-scores-block';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GenomicScoresBlockService {
  private http = inject(HttpClient);
  private config = inject(ConfigService);

  private readonly genomicScoresUrl = 'genomic_scores';

  public getGenomicScores(): Observable<GenomicScore[]> {
    return this.http
      .get(this.config.baseUrl + this.genomicScoresUrl).pipe(
        map((res: object[]) => GenomicScore.fromJsonArray(res))
      );
  }
}
