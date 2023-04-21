import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { ConfigService } from '../config/config.service';
import { AuthService } from 'app/auth.service';
import { map } from 'rxjs/operators';

@Injectable()
export class GeneSetsService {
  private readonly geneSetsCollectionsUrl = 'gene_sets/gene_sets_collections';
  private readonly geneSetsSearchUrl = 'gene_sets/gene_sets';

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private authService: AuthService
  ) {}

  public getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .get(this.config.baseUrl + this.geneSetsCollectionsUrl, options)
      .pipe(map((res: any) => GeneSetsCollection.fromJsonArray(res)));
  }

  public getGeneSets(
    selectedGeneSetsCollection: string,
    searchTerm: string,
    geneSetsTypes: object
  ): Observable<GeneSet[]> {
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.geneSetsSearchUrl, {
        geneSetsCollection: selectedGeneSetsCollection,
        filter: searchTerm,
        geneSetsTypes: geneSetsTypes,
        limit: 100
      }, options)
      .pipe(map((res: any) => GeneSet.fromJsonArray(res)));
  }

  public downloadGeneSet(geneSet: GeneSet): Promise<Response> {
    const headers = {'Content-Type': 'application/json'};
    headers['Authorization'] = `Bearer ${this.authService.getAccessToken()}`;
    return fetch(`${this.config.baseUrl}${geneSet.download}`, {
      credentials: 'include',
      headers: headers,
    });
  }
}
