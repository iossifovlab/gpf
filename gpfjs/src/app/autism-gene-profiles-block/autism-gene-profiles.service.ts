import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { GeneProfilesSingleViewConfig, GeneProfilesGene } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { ConfigService } from 'app/config/config.service';
import { plainToClass } from 'class-transformer';
// eslint-disable-next-line no-restricted-imports
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class GeneProfilesService {
  private readonly configUrl = 'autism_gene_tool/single-view/configuration';
  private readonly genesUrl = 'autism_gene_tool/single-view/gene/';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getConfig(): Observable<GeneProfilesSingleViewConfig> {
    return this.http
      .get(this.config.baseUrl + this.configUrl).pipe(
        map(res => {
          if (Object.keys(res).length === 0) {
            return;
          }
          return plainToClass(GeneProfilesSingleViewConfig, res);
        })
      );
  }

  public getGene(geneSymbol: string): Observable<GeneProfilesGene> {
    return this.http
      .get(this.config.baseUrl + this.genesUrl + geneSymbol)
      .pipe(map(res => plainToClass(GeneProfilesGene, res)), catchError(() => of(null)));
  }
}
