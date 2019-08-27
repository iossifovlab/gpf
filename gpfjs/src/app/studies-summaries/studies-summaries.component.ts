import { Component, OnInit } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { PopupComponent } from '../popup/popup.component';

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
    private studiesSummariesService: StudiesSummariesService,
    private modalService: NgbModal
  ) { }

  ngOnInit() {
    this.studiesSummaries$ = this.studiesSummariesService.getStudiesSummaries()
      .share();
  }

  showDescription(desc) {
    const modalRef = this.modalService.open(PopupComponent, {
      size: 'lg'
    });
    modalRef.componentInstance.data = desc;
  }
}
