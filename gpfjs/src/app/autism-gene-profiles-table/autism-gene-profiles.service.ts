import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile-table';

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

  getConfig(): Observable<AutismGeneToolConfig> {
    return this.http
    .get(this.config.baseUrl + this.configUrl)
    .map(res => {
      if (Object.keys(res).length === 0) {
        return;
      }

      return AutismGeneToolConfig.fromJson(res);
    });
  }

  getGene(geneSymbol: string): Observable<AutismGeneToolGene> {
    return this.http
    .get(this.config.baseUrl + this.genesUrl + geneSymbol)
    .map(res => {
      return AutismGeneToolGene.fromJson(res);
    });
  }

  getGenes(page: number, searchString?: string, sortBy?: string, order?: string): Observable<AutismGeneToolGene[]> {
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

    return this.http
      .get(url)
      .map(res => {
        return (res as Array<Object>)
          .map(gene => AutismGeneToolGene.fromJson(gene));
      });
  }
}
