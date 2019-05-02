import { Injectable } from '@angular/core';
import { Http } from '@angular/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { GenomicScores } from './genomic-scores-block';
import { ConfigService } from '../config/config.service';



@Injectable()
export class GenomicScoresBlockService {
  private genomicScoresUrl = 'genomic_scores';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getGenomicScores(): Observable<GenomicScores[]> {
    return this.http
      .get(this.genomicScoresUrl)
      .map(res => {
        return GenomicScores.fromJsonArray(res.json());
      });
  }
}
