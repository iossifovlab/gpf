import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { StudyFilterState, StudyDescriptor } from './study-filter-store';

@Component({
  selector: 'gpf-study-filter',
  templateUrl: './study-filter.component.html',
  styleUrls: ['./study-filter.component.css']
})
export class StudyFilterComponent {
  @Input() studyFilterState: StudyFilterState;
  @Input() errors: string[];
  @Input() studies: StudyDescriptor[];

  constructor() { }

  set selectedStudyNames(selectedStudyId: string) {
    for(let study of this.studies) {
      if (study.studyId === selectedStudyId) {
        this.studyFilterState.study = study;
        break;
      }
    }
  }

  get selectedStudyNames() {
    return this.studyFilterState.study.studyId;
  }
}
