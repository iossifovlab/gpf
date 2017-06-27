import { Input, Component, OnInit } from '@angular/core';

import { Observable, BehaviorSubject } from 'rxjs';

import { IntervalForVertex } from '../utils/interval-sandwich';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import {
  PerfectlyDrawablePedigreeService
} from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { Individual, MatingUnit } from './pedigree-data';

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
  matingUnits$: Observable<MatingUnit[]>;

  constructor(
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService
  ) { }

  ngOnInit() {
    let sandwichResults$ = this.family$
      .filter(f => !!f)
      .map(family => this.perfectlyDrawablePedigreeService.isPDP(family))
      .share();

    this.matingUnits$ = sandwichResults$
      .map(([, intervals]) => intervals)
      .filter(i => !!i)
      .map(intervals => {
        let individuals: IntervalForVertex<Individual>[] = intervals
          .filter(interval => interval.vertex instanceof Individual)
          .map(i => i as IntervalForVertex<Individual>);


        let matingUnits = individuals
          .reduce((acc, interval) => {
            interval.vertex.matingUnits.forEach(m => acc.push(m));
            return acc;
          }, [] as MatingUnit[]);

        return Array.from(new Set(matingUnits));
      })
      .share();

    this.isPdp$ = sandwichResults$
      .map(([, intervals]) => !!intervals);
  }


}
