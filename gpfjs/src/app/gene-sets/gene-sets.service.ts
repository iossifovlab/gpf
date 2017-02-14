import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

@Injectable()
export class GeneSetsService {
  private geneSetsUrl = 'gene_sets';
  private geneSetsSearchUrl = 'gene_sets_list';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    return this.http
      .get(this.geneSetsUrl)
      .map(res => {
        return GeneSetsCollection.fromJsonArray(res.json().gene_sets);
      });
  }

  getGeneSets(): Observable<GeneSet[]> {
    return this.http
      .get(this.geneSetsSearchUrl)
      .map(res => {
        return GeneSet.fromJsonArray(res.json());
      });
  }
}
