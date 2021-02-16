import { HttpClient } from '@angular/common/http';
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
      return AutismGeneToolConfig.fromJson(res);
    });
  }

  getGenes(): Observable<AutismGeneToolGene[]> {
    return this.http
    .get(this.config.baseUrl + this.genesUrl)
    .map(res => {
      return (res as Array<Object>).map(gene => AutismGeneToolGene.fromJson(gene));
    });
  }
}
