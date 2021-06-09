import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Gene } from './gene';

@Injectable({
  providedIn: 'root'
})
export class GeneService {
  private readonly geneVisualizationUrl = 'genome/gene_models/default/';
  private readonly geneSymbolSearchUrl = 'genome/gene_models/search/';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
  ) {}

  getGene(geneSymbol: string) {
    return this.http
    .get(this.config.baseUrl + this.geneVisualizationUrl + geneSymbol)
    .map((response: any) => Gene.fromJson(response));
  }

  searchGenes(searchTerm: string) {
    return this.http.get(this.config.baseUrl + this.geneSymbolSearchUrl + searchTerm);
  }
}
