import { Component, OnInit } from '@angular/core';

import { Observable } from 'rxjs';

import { StudiesSummariesService } from './studies-summaries.service';
import { StudiesSummaries, StudySummary } from './studies-summaries';

@Component({
  selector: 'gpf-studies-summaries',
  templateUrl: './studies-summaries.component.html',
  styleUrls: ['./studies-summaries.component.css']
})
export class StudiesSummariesComponent implements OnInit {

  studiesSummaries$: Observable<StudiesSummaries>;
  columnNameToFieldName = StudySummary.columnNameToFieldName;

  constructor(
    private studiesSummariesService: StudiesSummariesService
  ) { }

  ngOnInit() {
    this.studiesSummaries$ = this.studiesSummariesService.getStudiesSummaries()
      .share();
  }

}
