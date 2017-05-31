import { Component, OnInit } from '@angular/core';

import { Observable } from 'rxjs';

import { StudiesSummariesService } from './studies-summaries.service';
import { StudiesSummaries, StudySummary } from './studies-summaries';
import { SELECTED_REPORT_QUERY_PARAM } from '../variant-reports/variant-reports.component';

@Component({
  selector: 'gpf-studies-summaries',
  templateUrl: './studies-summaries.component.html',
  styleUrls: ['./studies-summaries.component.css']
})
export class StudiesSummariesComponent implements OnInit {

  studiesSummaries$: Observable<StudiesSummaries>;
  columnNameToFieldName = StudySummary.columnNameToFieldName;
  SELECTED_REPORT_QUERY_PARAM = SELECTED_REPORT_QUERY_PARAM;

  constructor(
    private studiesSummariesService: StudiesSummariesService
  ) { }

  ngOnInit() {
    this.studiesSummaries$ = this.studiesSummariesService.getStudiesSummaries()
      .share();
  }

  getQueryParamObject(value) {
    let result = {};
    result[SELECTED_REPORT_QUERY_PARAM] = value;
    return result;
  }

}
