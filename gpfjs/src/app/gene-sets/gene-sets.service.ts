import { Injectable } from '@angular/core';
import { Headers, Http, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import { GeneSetsCollection, GeneSet } from './gene-sets';
import { ConfigService } from '../config/config.service';



@Injectable()
export class GeneSetsService {
  private geneSetsCollectionsUrl = 'gene_sets/gene_sets_collections';
  private geneSetsSearchUrl = 'gene_sets/gene_sets';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    const headers = new Headers({ 'Content-Type': 'application/json' });
    const options = new RequestOptions({ headers: headers, withCredentials: true });
    return this.http
      .get(this.geneSetsCollectionsUrl, options)
      .map(res => {
        return GeneSetsCollection.fromJsonArray(res.json());
      });
  }

  getGeneSets(selectedGeneSetsCollection: string, searchTerm: string, geneSetsTypes: Object): Observable<GeneSet[]> {
    const headers = new Headers({ 'Content-Type': 'application/json' });
    const options = new RequestOptions({ headers: headers, withCredentials: true });
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
