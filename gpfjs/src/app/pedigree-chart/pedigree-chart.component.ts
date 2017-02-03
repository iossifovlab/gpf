import { Input, Component, OnInit } from '@angular/core';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';

@Component({
  selector: 'gpf-pedigree-chart',
  templateUrl: './pedigree-chart.component.html'
})
export class PedigreeChartComponent {
  @Input() pedigreeData: PedigreeData[][];
}


