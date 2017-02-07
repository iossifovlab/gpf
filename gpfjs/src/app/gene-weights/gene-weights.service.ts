import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';
import { GeneWeights, Partitions } from './gene-weights';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

@Injectable()
export class GeneWeightsService {
  private geneWeightsUrl = 'gene_weights';
  private geneWeightsPartitionsUrl = 'gene_weights/partition';

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
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers });
    return this.http
      .post(this.geneWeightsPartitionsUrl, {}, options)
      .map(res => {
        return Partitions.fromJson(res.json());
      });
  }
}
