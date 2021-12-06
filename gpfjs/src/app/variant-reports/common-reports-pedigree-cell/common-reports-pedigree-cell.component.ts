import { Component, OnInit, Input } from '@angular/core';
import { PedigreeCounter } from '../variant-reports';

@Component({
  selector: 'gpf-common-reports-pedigree-cell',
  templateUrl: './common-reports-pedigree-cell.component.html',
  styleUrls: ['./common-reports-pedigree-cell.component.css']
})
export class CommonReportsPedigreeCellComponent implements OnInit {
  @Input() pedigree: PedigreeCounter;

  constructor() { }

  ngOnInit(): void {
  }

}
