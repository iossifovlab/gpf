import { StudyTypes } from './study-types';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';

import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider } from '../query/query-state-provider';
import { QueryData } from '../query/query';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
  styleUrls: ['./study-types.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => StudyTypesComponent) }]

})
export class StudyTypesComponent extends QueryStateProvider implements OnInit {

  studyTypes = new StudyTypes();

  errors: string[];
  flashingAlert = false;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .subscribe(state => {
          if (state['studyType']) {
            for (let studyType of state['studyType']) {
              if (studyType === 'we') {
                this.studyTypes.we = true;
              }
              if (studyType === 'tg') {
                this.studyTypes.tg = true;
              }
            }
          }
        });
  }

  selectAll(): void {
    this.studyTypes.tg = true;
    this.studyTypes.we = true;
  }

  selectNone(): void {
    this.studyTypes.tg = false;
    this.studyTypes.we = false;
  }

  studyTypesCheckValue(studyType: string, value: boolean): void {
    if (studyType === 'we') {
      this.studyTypes.we = value;
    } else if (studyType === 'tg') {
      this.studyTypes.tg = value;
    }
  }

  getState() {
    return toValidationObservable(this.studyTypes)
      .map(statue =>
        ({ studyTypes: QueryData.trueFalseToStringArray(this.studyTypes) }))
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);

        return Observable.throw(`${this.constructor.name}: invalid measure state`);
    });
  }

}
