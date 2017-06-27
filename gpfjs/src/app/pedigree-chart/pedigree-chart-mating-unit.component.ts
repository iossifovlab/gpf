import { Input, Component, OnInit } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { Individual, MatingUnitWithIntervals, PedigreeDataWithPosition, Line } from './pedigree-data';
import { IntervalForVertex } from '../utils/interval-sandwich';

@Component({
  selector: '[gpf-pedigree-chart-mating-unit]',
  templateUrl: './pedigree-chart-mating-unit.component.html'
})
export class PedigreeChartMatingUnitComponent implements OnInit {
  pedigreeDataWithLayout: PedigreeDataWithPosition[];
  lines: Line[];

  SIZE = 21;
  SCALE = 1.0;

  @Input() matingUnit: MatingUnitWithIntervals;

  ngOnInit() {
    this.pedigreeDataWithLayout = this.generateMembersLayout(this.matingUnit);
    this.lines = this.generateLines(this.matingUnit);
  }

  generateMembersLayout(matingUnit: MatingUnitWithIntervals) {
    let pedigreeDataWithLayout = new Array<PedigreeDataWithPosition>();

    let intervals = new Array<IntervalForVertex<Individual>>();

    intervals.push(matingUnit.mother);
    intervals.push(matingUnit.mother);
    matingUnit.children.forEach(child => {
      intervals.push(child);
    });

    this.fixRank(this.translateIntervalsToZero(intervals))
      .forEach(interval => {
      pedigreeDataWithLayout.push(this.getPedigreeWithPosition(interval));
    });


    return pedigreeDataWithLayout;
  }

  getPedigreeWithPosition(interval: IntervalForVertex<Individual>) {
    return new PedigreeDataWithPosition(
      interval.vertex.pedigreeData, interval.left * 15, interval.vertex.rank * 40,
      this.SIZE, this.SCALE
    );
  }

  generateLines(matingUnit) {
    return [];
  }

  translateIntervalsToZero(intervals: Array<IntervalForVertex<Individual>>) {
    let min = intervals.map(interval => interval.left)
      .reduce((acc, current) => {
        console.log("current:", current);
        return Math.min(acc, current)
      });

    return intervals.map(interval => {
      let copy = interval.copy();

      copy.left -= min;
      copy.right -= min;

      return copy;
    });
  }

  fixRank(intervals: Array<IntervalForVertex<Individual>>) {
    let maxRank = intervals.map(interval => interval.vertex.rank)
      .reduce((acc, current) => Math.max(acc, current), 0);

    return intervals.map(interval => {
      interval.vertex.rank -= maxRank;
      interval.vertex.rank = -interval.vertex.rank;
      return interval;
    });
  }

}
