import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AgpSingleViewConfig, AgpGene } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { ConfigService } from 'app/config/config.service';
import { plainToClass } from 'class-transformer';
// eslint-disable-next-line no-restricted-imports
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AutismGeneProfilesService {
  private readonly configUrl = 'autism_gene_tool/single-view/configuration';
  private readonly genesUrl = 'autism_gene_tool/single-view/gene/';

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  public getConfig(): Observable<AgpSingleViewConfig> {
    return this.http
      .get(this.config.baseUrl + this.configUrl).pipe(
        map(res => {
          if (Object.keys(res).length === 0) {
            return;
          }
          return plainToClass(AgpSingleViewConfig, res);
        })
      );
  }

  public getGene(geneSymbol: string): Observable<AgpGene> {
    return this.http
      .get(this.config.baseUrl + this.genesUrl + geneSymbol)
      .pipe(map(res => plainToClass(AgpGene, res)));
  }
}
