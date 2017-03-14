import { StudyTypesState, STUDY_TYPES_CHECK_ALL, STUDY_TYPES_UNCHECK_ALL, STUDY_TYPES_UNCHECK, STUDY_TYPES_CHECK } from './study-types';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
  styleUrls: ['./study-types.component.css']
})
export class StudyTypesComponent implements OnInit {
  we: boolean = true;
  tg: boolean = true;

  studyTypesState: Observable<[StudyTypesState, boolean, ValidationError[]]>;

  private errors: string[];

  constructor(
    private store: Store<any>
  ) {

    this.studyTypesState = toObservableWithValidation(StudyTypesState, this.store.select('studyTypes'));
  }

  ngOnInit() {
    this.studyTypesState.subscribe(
      ([state, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

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
