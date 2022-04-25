import { Component, Input } from '@angular/core';
import { PedigreeCounter } from '../variant-reports';

@Component({
  selector: 'gpf-common-reports-pedigree-cell',
  templateUrl: './common-reports-pedigree-cell.component.html',
  styleUrls: ['./common-reports-pedigree-cell.component.css']
})
export class CommonReportsPedigreeCellComponent {
  @Input() public pedigree: PedigreeCounter;
}
