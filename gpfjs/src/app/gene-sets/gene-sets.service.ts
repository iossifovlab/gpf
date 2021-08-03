import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { GeneSetsCollection, GeneSet } from './gene-sets';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GeneSetsService {
  private readonly geneSetsCollectionsUrl = 'gene_sets/gene_sets_collections';
  private readonly geneSetsSearchUrl = 'gene_sets/gene_sets';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .get(this.config.baseUrl + this.geneSetsCollectionsUrl, options)
      .pipe(map((res: any) => {
        return GeneSetsCollection.fromJsonArray(res);
      }));
  }

  getGeneSets(selectedGeneSetsCollection: string, searchTerm: string, geneSetsTypes: Object): Observable<GeneSet[]> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.geneSetsSearchUrl, {
        geneSetsCollection: selectedGeneSetsCollection,
        filter: searchTerm,
        geneSetsTypes: geneSetsTypes,
        limit: 100
      }, options)
      .pipe(map((res: any) => {
        return GeneSet.fromJsonArray(res);
      }));
  }
}
