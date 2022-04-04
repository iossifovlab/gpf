import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';

import { GeneScores, Partitions } from './gene-scores';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GeneScoresService {
  private readonly geneScoresUrl = 'gene_scores';
  private readonly geneScoresPartitionsUrl = 'gene_scores/partitions';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getGeneScores(geneScoresIds?: string): Observable<GeneScores[]> {
    let url = this.config.baseUrl + this.geneScoresUrl;

    if (geneScoresIds) {
      const searchParams = new HttpParams().set('ids', geneScoresIds);
      url += `?${searchParams.toString()}`;
    }

    return this.http.get(url).pipe(map((res: any) => {
      return GeneScores.fromJsonArray(res);
    }));
  }

  getPartitions(score: string, min: number, max: number): Observable<Partitions> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers };

    return this.http
      .post(this.config.baseUrl + this.geneScoresPartitionsUrl, {score: score, min: min, max: max}, options)
      .pipe(map((res: any) => {
        return Partitions.fromJson(res);
      }));
  }
}


// 1) search -> rename 
// 2) test(unit) 
