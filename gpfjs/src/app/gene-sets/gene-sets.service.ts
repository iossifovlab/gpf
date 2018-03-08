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
  private geneSetsCollectionsUrl = 'gene_sets/gene_sets_collections';
  private geneSetsSearchUrl = 'gene_sets/gene_sets';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers, withCredentials: true });
    return this.http
      .get(this.geneSetsCollectionsUrl, options)
      .map(res => {
        return GeneSetsCollection.fromJsonArray(res.json());
      });
  }

  getGeneSets(selectedGeneSetsCollection: string, searchTerm: string, geneSetsTypes: Object): Observable<GeneSet[]> {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers, withCredentials: true });
    return this.http
      .post(this.geneSetsSearchUrl, {
        geneSetsCollection: selectedGeneSetsCollection,
        filter: searchTerm,
        geneSetsTypes: geneSetsTypes,
        limit: 100
      }, options)
      .map(res => {
        return GeneSet.fromJsonArray(res.json());
      });
  }
}
