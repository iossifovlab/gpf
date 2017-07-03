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
    intervals.push(matingUnit.father);
    matingUnit.children.forEach(child => {
      intervals.push(child);
    });


    this.translateIntervalsToZero(intervals)
      .forEach(interval => {
      pedigreeDataWithLayout.push(this.getPedigreeWithPosition(interval));
    });


    return pedigreeDataWithLayout;
  }

  getPedigreeWithPosition(interval: IntervalForVertex<Individual>) {
    return new PedigreeDataWithPosition(
      interval.vertex.pedigreeData, interval.right * 20 + 15, interval.vertex.rank * 40 + 15,
      this.SIZE, this.SCALE
    );
  }

  generateLines(matingUnit: MatingUnitWithIntervals) {
    let lines = new Array<Line>();
    let motherPosition = this.getPedigreeWithPosition(matingUnit.mother);
    let fatherPosition = this.getPedigreeWithPosition(matingUnit.father);

    lines.push(new Line(
      motherPosition.xCenter, motherPosition.yCenter,
      fatherPosition.xCenter, fatherPosition.yCenter
    ));

    return lines;
  }

  translateIntervalsToZero(intervals: Array<IntervalForVertex<Individual>>) {
    let min = intervals.map(interval => interval.left)
      .reduce((acc, current) => {
        return Math.min(acc, current);
      });

    return intervals.map(interval => {
      let copy = interval.copy();

      copy.left -= min;
      copy.right -= min;

      return copy;
    });
  }

}
