import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';

import { Chromosome } from './chromosome';

@Injectable()
export class ChromosomeService {
  private readonly chromosomeUrl = 'chromosomes/';

  constructor(private http: HttpClient) {}

  getChromosomes(): Observable<Chromosome[]> {
    return this.http
      .get(this.chromosomeUrl)
      .map((response: any) => Chromosome.fromJsonArray(response));
  }
}
