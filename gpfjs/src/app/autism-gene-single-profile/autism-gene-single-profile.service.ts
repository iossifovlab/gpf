import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AutismGeneSingleProfileService {
  private readonly genesUrl = 'autism_gene_tool/genes/';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
  ) {}

  getGene(geneSymbol: string): Observable<AutismGeneToolGene> {
    return this.http
    .get(this.config.baseUrl + this.genesUrl + geneSymbol)
    .map(res => {
      return AutismGeneToolGene.fromJson(res);
    });
  }
}
