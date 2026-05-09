import { Input, Component } from '@angular/core';
import { PedigreeData } from '../genotype-preview-model/genotype-preview';

@Component({
  selector: '[gpf-pedigree-chart-member]',
  templateUrl: './pedigree-chart-member.component.html',
  standalone: false
})
export class PedigreeChartMemberComponent {
  @Input() public pedigreeData: PedigreeData;
}
