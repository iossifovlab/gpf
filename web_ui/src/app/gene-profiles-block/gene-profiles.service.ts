import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import {
  GeneProfilesSingleViewConfig,
  GeneProfilesGene
} from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { ConfigService } from 'app/config/config.service';
import { plainToClass } from 'class-transformer';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class GeneProfilesService {
  private http = inject(HttpClient);
  private config = inject(ConfigService);

  private readonly configUrl = 'gene_profiles/single-view/configuration';
  private readonly genesUrl = 'gene_profiles/single-view/gene/';

  public getConfig(): Observable<GeneProfilesSingleViewConfig> {
    return this.http
      .get(this.config.baseUrl + this.configUrl).pipe(
        map(res => {
          if (Object.keys(res).length === 0) {
            return;
          }
          return GeneProfilesSingleViewConfig.fromJson(res);
        })
      );
  }

  public getGene(geneSymbol: string): Observable<GeneProfilesGene> {
    return this.http
      .get(this.config.baseUrl + this.genesUrl + geneSymbol)
      .pipe(map(res => plainToClass(GeneProfilesGene, res)), catchError(() => of(null)));
  }
}
