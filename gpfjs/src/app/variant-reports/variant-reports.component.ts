import { Component, OnInit } from '@angular/core';

import { Observable, Subject } from 'rxjs';

import { VariantReportsService } from './variant-reports.service';
import { Studies, Study, VariantReport, ChildrenCounter } from './variant-reports';

@Component({
  selector: 'gpf-variant-reports',
  templateUrl: './variant-reports.component.html',
  styleUrls: ['./variant-reports.component.css']
})
export class VariantReportsComponent implements OnInit {

  reports$: Observable<Studies>;
  selectedReport$ = new Subject<Study>();

  variantReport$: Observable<VariantReport>;

  constructor(
    private variantReportsService: VariantReportsService
  ) { }

  ngOnInit() {
    this.reports$ = this.variantReportsService.getStudies();

    this.variantReport$ = this.selectedReport$
      .switchMap(study => this.variantReportsService.getVariantReport(study))
      .share();
  }

  selectReport(study: Study) {
    this.selectedReport$.next(study);
  }

  orderByColumnOrder(childrenCounters: ChildrenCounter[], columns: string[], strict = false) {
    let columnsLookup = new Map<string, number>(
      columns.map((value, index): [string, number] => [value, index])
    );

    let filteredChildrenCounters = childrenCounters
      .filter(
        childCounters => columnsLookup.has(childCounters.phenotype));

    if (strict && filteredChildrenCounters.length !== columns.length) {
      return [];
    }

    return filteredChildrenCounters.sort(
      (child1, child2) => {
        let index1 = columnsLookup.get(child1.phenotype);
        let index2 = columnsLookup.get(child2.phenotype);
        return index1 - index2;
      }
    );
  }

}
