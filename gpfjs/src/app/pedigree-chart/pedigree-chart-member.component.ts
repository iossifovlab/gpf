import { Input, Component, OnInit } from '@angular/core';
import { PedigreeData } from '../genotype-preview-model/genotype-preview';


@Component({
  selector: '[gpf-pedigree-chart-member]',
  templateUrl: './pedigree-chart-member.component.html'
})
export class PedigreeChartMemberComponent  {
  @Input() pedigreeData: PedigreeData
}
