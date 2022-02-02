import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
import { plainToClass } from 'class-transformer';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AgpTableConfig } from './autism-gene-profiles-table';

@Injectable({
  providedIn: 'root'
})
export class AgpTableService {
  private readonly configUrl = 'autism_gene_tool/table/configuration';
  private readonly genesUrl = 'autism_gene_tool/table/rows';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getConfig(): Observable<AgpTableConfig> {
    return this.http
      .get(this.config.baseUrl + this.configUrl).pipe(
        map(res => {
          if (Object.keys(res).length === 0) {
            return;
          }
          return plainToClass(AgpTableConfig, res);
        })
      );
  }

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
}
