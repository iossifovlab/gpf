import { Injectable } from '@angular/core';
import { Http } from '@angular/http';

import { Chromosome } from './chromosome';

@Injectable()
export class ChromosomeService {

  chromosomeUrl = 'chromosomes/';

  constructor(private http: Http) { }

  getChromosomes(): Promise<Chromosome[]> {
    return this.http
      .get(this.chromosomeUrl)
      .map(response => Chromosome.fromJsonArray(response.json()))
      .toPromise();
  }
}
