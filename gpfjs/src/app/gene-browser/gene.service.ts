import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Gene } from './gene';
import { map } from 'rxjs/operators';

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

  public getGene(geneSymbol: string) {
    return this.http
    .get(this.config.baseUrl + this.geneVisualizationUrl + geneSymbol)
    .pipe(map((response: object) => Gene.fromJson(response)));
  }

  public searchGenes(searchTerm: string) {
    return this.http.get(this.config.baseUrl + this.geneSymbolSearchUrl + searchTerm.toUpperCase());
  }
}
