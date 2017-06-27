import { Input, Component, OnInit } from '@angular/core';

import { Observable, BehaviorSubject } from 'rxjs';

import { IntervalForVertex } from '../utils/interval-sandwich';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import {
  PerfectlyDrawablePedigreeService
} from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { MatingUnitWithIntervals, IndividualSet, Individual, MatingUnit } from './pedigree-data';

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
  matingUnits$: Observable<MatingUnitWithIntervals[]>;

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
        return this.getMatingUnitsFromIntervals(intervals);
      })
      .share();

    this.isPdp$ = sandwichResults$
      .map(([, intervals]) => !!intervals);
  }

  getMatingUnitsFromIntervals(intervals: IntervalForVertex<IndividualSet>[]) {
    let individuals: IntervalForVertex<Individual>[] = intervals
      .filter(interval => interval.vertex instanceof Individual)
      .map(i => i as IntervalForVertex<Individual>);

    let individualIntervalMap = new Map<string, IntervalForVertex<Individual>>(
      individuals.map((interval): [string, IntervalForVertex<Individual>] =>
        [interval.vertex.toString(), interval])
    );


    let matingUnits = individuals
      .reduce((acc, interval) => {
        interval.vertex.matingUnits.forEach(m => acc.push(m));
        return acc;
      }, [] as MatingUnit[]);

    let uniqueMatingUnits = Array.from(new Set(matingUnits));

    let result = new Array<MatingUnitWithIntervals>();

    for (let matingUnit of uniqueMatingUnits) {
      let matingUnitIntervals = new MatingUnitWithIntervals(
        individualIntervalMap.get(matingUnit.mother.toString()),
        individualIntervalMap.get(matingUnit.father.toString()),
        matingUnit.children.individuals
          .map(i => individualIntervalMap.get(i.toString())),
      );

      result.push(matingUnitIntervals);
    }

    return result;
  }


}
