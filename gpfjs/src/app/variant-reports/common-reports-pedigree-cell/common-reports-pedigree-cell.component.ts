import { Component, OnInit, Input } from '@angular/core';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';

@Component({
  selector: 'gpf-common-reports-pedigree-cell',
  templateUrl: './common-reports-pedigree-cell.component.html',
  styleUrls: ['./common-reports-pedigree-cell.component.css']
})
export class CommonReportsPedigreeCellComponent implements OnInit {
  @Input() pedigree: PedigreeData;

  constructor() { }

  ngOnInit(): void {
  }

}
