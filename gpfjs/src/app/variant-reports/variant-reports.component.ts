import { Component, OnInit } from '@angular/core';

import { Observable, Subject } from 'rxjs';

import { VariantReportsService } from './variant-reports.service';
import { Studies, Study } from './variant-reports';

@Component({
  selector: 'gpf-variant-reports',
  templateUrl: './variant-reports.component.html',
  styleUrls: ['./variant-reports.component.css']
})
export class VariantReportsComponent implements OnInit {

  reports$: Observable<Studies>;
  selectedReport$ = new Subject<Study>();

  constructor(
    private variantReportsService: VariantReportsService
  ) { }

  ngOnInit() {
    this.reports$ = this.variantReportsService.getStudies();
  }

  selectReport(study: Study) {
    this.selectedReport$.next(study);
  }

}
