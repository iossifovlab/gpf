import { Injectable } from '@angular/core';
import { Headers, Http, RequestOptions } from '@angular/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { GeneWeights, Partitions } from './gene-weights';
import { ConfigService } from '../config/config.service';



@Injectable()
export class GeneWeightsService {
  private geneWeightsUrl = 'gene_weights';
  private geneWeightsPartitionsUrl = 'gene_weights/partitions';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getGeneWeights(): Observable<GeneWeights[]> {
    return this.http
      .get(this.geneWeightsUrl)
      .map(res => {
        return GeneWeights.fromJsonArray(res.json());
      });
  }

  getPartitions(weight: string, min: number, max: number): Observable<Partitions> {
    const headers = new Headers({ 'Content-Type': 'application/json' });
    const options = new RequestOptions({ headers: headers });
    return this.http
      .post(this.geneWeightsPartitionsUrl, {weight: weight, min: min, max: max}, options)
      .map(res => {
        return Partitions.fromJson(res.json());
      });
  }
}
