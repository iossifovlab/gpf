import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AgpConfig, AgpGene } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { ConfigService } from 'app/config/config.service';
import { plainToClass } from 'class-transformer';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AutismGeneProfilesService {
  private readonly configUrl = 'autism_gene_tool/configuration';
  private readonly genesUrl = 'autism_gene_tool/genes/';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
  ) {}

  getConfig(): Observable<AgpConfig> {
    return this.http
    .get(this.config.baseUrl + this.configUrl).pipe(
      map(res => {
        if (Object.keys(res).length === 0) {
          return;
        }
        return plainToClass(AgpConfig, res);
      })
    );
  }

  getGene(geneSymbol: string): Observable<AgpGene> {
    return this.http
    .get(this.config.baseUrl + this.genesUrl + geneSymbol).pipe(
      map(res => {
        return plainToClass(AgpGene, res);
      })
    );
  }

  getGenes(page: number, searchString?: string, sortBy?: string, order?: string): Observable<AgpGene[]> {
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

    url += `?${params}`;

    return this.http.get(url).pipe(
      map(res => {
        return (res as Array<Object>)
          .map(gene => plainToClass(AgpGene, gene));
      })
    );
  }
}
