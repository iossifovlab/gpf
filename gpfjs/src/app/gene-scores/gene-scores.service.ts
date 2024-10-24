import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GeneScores, Partitions } from './gene-scores';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GeneScoresService {
  private readonly geneScoresUrl = 'gene_scores';
  private readonly geneScoresPartitionsUrl = 'gene_scores/partitions';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getGeneScores(geneScoresIds?: string): Observable<GeneScores[]> {
    let url = this.config.baseUrl + this.geneScoresUrl + '/histograms';
    if (geneScoresIds) {
      const searchParams = new HttpParams().set('ids', geneScoresIds);
      url += `?${searchParams.toString()}`;
    }
    return this.http.get(url).pipe(map((res: GeneScores[]) => GeneScores.fromJsonArray(res)));
  }

  public getPartitions(score: string, min: number, max: number): Observable<Partitions> {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers };

    return this.http
      .post(this.config.baseUrl + this.geneScoresPartitionsUrl, {score: score, min: min, max: max}, options)
      .pipe(map((res: Partitions) => Partitions.fromJson(res)));
  }
}
