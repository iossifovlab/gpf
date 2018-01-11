import { Injectable } from '@angular/core';
import { Http } from '@angular/http';

import { Chromosome, ChromosomeBand } from './chromosome';

@Injectable()
export class ChromosomeService {

  chromosomeUrl: string = 'chromosomes/';

  constructor(private http: Http) { }

  getChromosomes(): Promise<Chromosome[]> {
    return this.http
      .get(this.chromosomeUrl)
      .map(response => Chromosome.fromJsonArray(response.json()))
      .toPromise();
  }
}
