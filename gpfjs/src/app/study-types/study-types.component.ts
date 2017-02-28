import { StudyTypesState, STUDY_TYPES_CHECK_ALL, STUDY_TYPES_UNCHECK_ALL, STUDY_TYPES_UNCHECK, STUDY_TYPES_CHECK } from './study-types';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';



@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
  styleUrls: ['./study-types.component.css']
})
export class StudyTypesComponent implements OnInit {
  we: boolean = true;
  tg: boolean = true;

  studyTypesState: Observable<StudyTypesState>;

  constructor(
    private store: Store<any>
  ) {

    this.studyTypesState = this.store.select('studyTypes');
  }

  ngOnInit() {
    this.studyTypesState.subscribe(
      state => {
        this.we = state.we;
        this.tg = state.tg;
      }
    );
  }

  selectAll(): void {
    this.store.dispatch({
      'type': STUDY_TYPES_CHECK_ALL,
    });
  }

  selectNone(): void {
    this.store.dispatch({
      'type': STUDY_TYPES_UNCHECK_ALL,
    });
  }

  studyTypesCheckValue(studyType: string, value: boolean): void {
    if (studyType === 'we' || studyType === 'tg') {
      this.store.dispatch({
        'type': value ? STUDY_TYPES_CHECK : STUDY_TYPES_UNCHECK,
        'payload': studyType
      });
    }
  }


}
