import { Input, Component, OnInit } from '@angular/core';

import { Observable, BehaviorSubject } from 'rxjs';

import { IntervalForVertex } from '../utils/interval-sandwich';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import {
  PerfectlyDrawablePedigreeService
} from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { MatingUnitWithIntervals, IndividualSet, Individual, MatingUnit } from './pedigree-data';

type OrderedIndividuals = Array<Individual>;

@Component({
  selector: 'gpf-pedigree-chart',
  templateUrl: './pedigree-chart.component.html'
})
export class PedigreeChartComponent implements OnInit {

  @Input()
  set family(data: PedigreeData[]) {
    this.family$.next(data);
  }

  private family$ = new BehaviorSubject<PedigreeData[]>(null);
  private isPdp$: Observable<boolean>;
  levels$: Observable<Array<OrderedIndividuals>>;

  constructor(
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService
  ) { }

  ngOnInit() {
    let sandwichResults$ = this.family$
      .filter(f => !!f)
      .map(family => this.perfectlyDrawablePedigreeService.isPDP(family))
      .share();

    this.levels$ = sandwichResults$
      .map(([, intervals]) => intervals)
      .filter(i => !!i)
      .map(i => this.onlyInidividuals(i))
      .map(i => this.getIndividualsByRank(i))
      .share();

    this.isPdp$ = sandwichResults$
      .map(([, intervals]) => !!intervals);
  }

  getIndividualsByRank(individuals: IntervalForVertex<Individual>[]) {
    let individualsByRank = individuals.reduce((acc, individual) => {
      if (acc.has(individual.vertex.rank)) {
        acc.get(individual.vertex.rank).push(individual);
      } else {
        acc.set(individual.vertex.rank, [individual]);
      }
      return acc;
    }, new Map<number, IntervalForVertex<Individual>[]>());

    let keys: Array<number> = [];
    let rankIterator = individualsByRank.keys();
    let itResult = rankIterator.next();
    while (!itResult.done) {
      keys.push(itResult.value);
      itResult = rankIterator.next();
    }

    let result: OrderedIndividuals[] = [];
    for (let key of keys.sort()) {
        let sorted = individualsByRank.get(key)
          .sort((a, b) => a.left - b.left);

        result.push(sorted.map(interval => interval.vertex));
    }

    return result;
  }

  onlyInidividuals(intervals: IntervalForVertex<IndividualSet>[]) {
    return intervals
        .filter(interval => interval.vertex instanceof Individual)
        .map(i => i as IntervalForVertex<Individual>);
  }


}
