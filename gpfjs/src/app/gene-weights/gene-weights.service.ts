import { Injectable } from '@angular/core';
import { Headers, Http, Response } from '@angular/http';
import { Observable } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';
import { GeneWeights } from './gene-weights';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

@Injectable()
export class GeneWeightsService {
  private geneWeightsUrl = 'gene_weights';

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
}
