import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { StudyFilterState } from './study-filter-store';

@Component({
  selector: 'gpf-study-filter',
  templateUrl: './study-filter.component.html',
  styleUrls: ['./study-filter.component.css']
})
export class StudyFilterComponent {
  @Input() studyFilterState: StudyFilterState;
  @Input() errors: string[];
  @Input() studies: string[];

  constructor() { }

  set selectedStudyNames(selectedStudyName: string) {
    this.studyFilterState.studyName = selectedStudyName;
  }

  get selectedStudyNames() {
    return this.studyFilterState.studyName;
  }
}
