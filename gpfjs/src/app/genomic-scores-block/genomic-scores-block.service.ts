import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { GenomicScores } from './genomic-scores-block';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GenomicScoresBlockService {
  private readonly genomicScoresUrl = 'genomic_scores';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getGenomicScores(): Observable<GenomicScores[]> {
    return this.http
      .get(this.config.baseUrl + this.genomicScoresUrl).pipe(
        map((res: any) => {
          return GenomicScores.fromJsonArray(res);
        })
      );
  }
}
