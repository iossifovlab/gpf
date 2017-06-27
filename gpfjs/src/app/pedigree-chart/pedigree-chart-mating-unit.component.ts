import { Input, Component, OnInit } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { Individual, MatingUnit, PedigreeDataWithPosition, Line } from './pedigree-data';
import { IntervalForVertex } from '../utils/interval-sandwich';

@Component({
  selector: '[gpf-pedigree-chart-mating-unit]',
  templateUrl: './pedigree-chart-mating-unit.component.html'
})
export class PedigreeChartMatingUnitComponent implements OnInit {
  pedigreeDataWithLayout: PedigreeDataWithPosition[];
  lines: Line[];

  @Input() matingUnit: MatingUnit;

  ngOnInit() {
    this.pedigreeDataWithLayout = this.generateMembersLayout(this.matingUnit);
    this.lines = this.generateLines(this.matingUnit);
  }

  generateMembersLayout(matingUnit: MatingUnit) {
    let pedigreeDataWithLayout = new Array<PedigreeDataWithPosition>();

    // matingUnit.father.
    console.log(matingUnit);
    return [];
  }

  generateLines(matingUnit) {
    return [];
  }

}
