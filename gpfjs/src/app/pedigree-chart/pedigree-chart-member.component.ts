import { Input, Component, OnInit } from '@angular/core';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';


@Component({
  selector: '[gpf-pedigree-chart-member]',
  templateUrl: './pedigree-chart-member.component.html'
})
export class PedigreeChartMemberComponent  {
  @Input() pedigreeData: PedigreeData
}
