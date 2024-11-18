import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GeneScore } from './gene-scores';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GeneScoresService {
  private readonly geneScoresUrl = 'gene_scores';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getGeneScores(geneScoresIds?: string): Observable<GeneScore[]> {
    let url = this.config.baseUrl + this.geneScoresUrl + '/histograms';
    if (geneScoresIds) {
      const searchParams = new HttpParams().set('ids', geneScoresIds);
      url += `?${searchParams.toString()}`;
    }
    return this.http.get(url).pipe(map((res: GeneScore[]) => GeneScore.fromJsonArray(res)));
  }
}
