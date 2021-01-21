import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'app/config/config.service';

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
    .map(res => {
      return res;
    })
  }

  getGenes() {
    return this.http
    .get(this.config.baseUrl + this.genesUrl)
    .map(res => {
      return res;
    })
  }
}
