import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions, URLSearchParams } from '@angular/http';
import { Observable } from 'rxjs';

import { GenomicScores } from './genomic-scores-block';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

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
