import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
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

  getConfig() {
    return this.http
    .get(this.config.baseUrl + this.configUrl)
    .map(res => AutismGeneToolConfig.fromJson(res))
  }

  getGenes() {
    return this.http
    .get(this.config.baseUrl + this.genesUrl)
    .map(res => {
      console.log(res)
      const geneArray: AutismGeneToolGene[] = [];
      (res as Array<Object>).map(gene => AutismGeneToolGene.fromJson(gene))
      return geneArray;
    })
  }

  getGenes1() {
    return this.http
    .get(this.config.baseUrl + this.genesUrl)
    .map(res => res)
  }
}
