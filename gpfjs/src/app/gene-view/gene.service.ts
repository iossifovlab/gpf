import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Gene } from './gene';

@Injectable({
  providedIn: 'root'
})
export class GeneService {
  private readonly geneVisualizationUrl = 'genome/gene_models/default/';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
  ) {}

  // http://localhost:8000/api/v3/genome/gene_models/default/CHD8
  // CHD8, FMR1, BRCA1
  getGene(geneSymbol: string) {
    return this.http
    .get(this.config.baseUrl + this.geneVisualizationUrl + geneSymbol)
    .map((response: any) => Gene.fromJson(response));
  }
}
