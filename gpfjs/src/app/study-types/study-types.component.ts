import { StudyTypes } from './study-types';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';

import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { QueryData } from '../query/query';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
  styleUrls: ['./study-types.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => StudyTypesComponent) }]

})
export class StudyTypesComponent extends QueryStateWithErrorsProvider implements OnInit {

  studyTypes = new StudyTypes();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['studyTypes']) {
          this.selectNone();
          for (let studyType of state['studyTypes']) {
            if (studyType === 'we') {
              this.studyTypes.we = true;
            }
            if (studyType === 'tg') {
              this.studyTypes.tg = true;
            }
            if (studyType === 'wg') {
              this.studyTypes.wg = true;
            }
          }
        }
      });
  }

  selectAll(): void {
    this.studyTypes.tg = true;
    this.studyTypes.we = true;
    this.studyTypes.wg = true;
  }

  selectNone(): void {
    this.studyTypes.tg = false;
    this.studyTypes.we = false;
    this.studyTypes.wg = false;
  }

  studyTypesCheckValue(studyType: string, value: boolean): void {
    if (studyType === 'we') {
      this.studyTypes.we = value;
    } else if (studyType === 'tg') {
      this.studyTypes.tg = value;
    } else if (studyType === 'wg') {
      this.studyTypes.wg = value;
    }
  }

  getState() {
    return this.validateAndGetState(this.studyTypes)
      .map(statue =>
        ({ studyTypes: QueryData.trueFalseToStringArray(this.studyTypes) }));
  }

}
