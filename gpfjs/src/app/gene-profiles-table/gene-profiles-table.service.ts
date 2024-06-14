import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class GeneProfilesTableService {
  private readonly genesUrl = 'gene_profiles/table/rows';
  private readonly geneSymbolsUrl = 'gene_profiles/table/gene_symbols/';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getGenes(page: number, searchString?: string, sortBy?: string, order?: string): Observable<any[]> {
    let url = this.config.baseUrl + this.genesUrl;
    let params = new HttpParams().set('page', page.toString());

    if (searchString) {
      params = params.append('symbol', searchString);
    }

    if (sortBy) {
      params = params.append('sortBy', sortBy);

      if (order) {
        params = params.append('order', order);
      }
    }

    url += `?${ params.toString() }`;

    return this.http.get(url).pipe(
      map(res => (res as Array<any>))
    );
  }

  public getGeneSymbols(page: number, searchString?: string): Observable<string[]> {
    let url = this.config.baseUrl + this.geneSymbolsUrl;
    let params = new HttpParams().set('page', page.toString());

    if (searchString) {
      params = params.append('symbol', searchString);
    }

    url += `?${ params.toString() }`;

    return this.http.get(url).pipe(
      map(res => (res as Array<string>))
    );
  }
}
