import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';

@Injectable({
  providedIn: 'root'
})
export class AutismGeneProfilesService {
  private readonly configUrl = 'autism_gene_tool/configuration';
  private readonly genesUrl = 'autism_gene_tool/genes';

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

  getGenes(page: number, geneSymbol: string): Observable<AutismGeneToolGene[]> {
    let url = this.config.baseUrl + this.genesUrl;

    let searchParams = new HttpParams().set('page', page.toString());
    if (geneSymbol) {
      searchParams = searchParams.append('symbol', geneSymbol);
    }

    url += `?${searchParams}`;

    return this.http
      .get(url)
      .map(res => {
        return (res as Array<Object>)
          .map(gene => AutismGeneToolGene.fromJson(gene));
      });
  }
}
