import { StudyTypesState, STUDY_TYPES_INIT, STUDY_TYPES_CHECK_ALL, STUDY_TYPES_UNCHECK_ALL, STUDY_TYPES_UNCHECK, STUDY_TYPES_CHECK } from './study-types';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { QueryStateProvider } from '../query/query-state-provider'
import { QueryData } from '../query/query'
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
  styleUrls: ['./study-types.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => StudyTypesComponent) }]

})
export class StudyTypesComponent extends QueryStateProvider implements OnInit {
  we: boolean = true;
  tg: boolean = true;

  studyTypesState: Observable<[StudyTypesState, boolean, ValidationError[]]>;

  private errors: string[];
  private flashingAlert = false;

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    super();
    this.studyTypesState = toObservableWithValidation(StudyTypesState, this.store.select('studyTypes'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': STUDY_TYPES_INIT,
    });

    this.stateRestoreService.state.subscribe(
      (state) => {
        if (state['studyType']) {
          this.store.dispatch({
            'type': STUDY_TYPES_UNCHECK_ALL,
          });

          for (let studyType of state['studyType']) {
            if (studyType === 'we' || studyType === 'tg') {
              this.store.dispatch({
                'type': STUDY_TYPES_CHECK,
                'payload': studyType
              });
            }
          }
        }
      }
    )

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

  getState() {
    return this.studyTypesState.take(1).map(
      ([studyTypesState, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid state"
        }
        return { studyType: QueryData.trueFalseToStringArray(studyTypesState) }
    });
  }

}
