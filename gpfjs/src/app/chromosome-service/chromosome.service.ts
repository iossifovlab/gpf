import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { Chromosome } from './chromosome';
import { ConfigService } from 'app/config/config.service';

@Injectable()
export class ChromosomeService {
  private readonly chromosomeUrl = 'chromosomes';

  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  getChromosomes(): Observable<Chromosome[]> {
    return this.http
      .get(this.config.baseUrl + this.chromosomeUrl)
      .map((response: any) => Chromosome.fromJsonArray(response));
  }
}
