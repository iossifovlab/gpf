import {
  GenderState, GENDER_CHECK_ALL, GENDER_INIT,
  GENDER_UNCHECK_ALL, GENDER_UNCHECK, GENDER_CHECK
} from './gender';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { QueryStateProvider } from '../query/query-state-provider'
import { QueryData } from '../query/query'
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GenderComponent) }]
})
export class GenderComponent extends QueryStateProvider implements OnInit {
  male: boolean = true;
  female: boolean = true;

  genderState: Observable<[GenderState, boolean, ValidationError[]]>;
  errors: string[];
  flashingAlert = false;

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    super();
    this.genderState = toObservableWithValidation(GenderState, this.store.select('gender'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': GENDER_INIT,
    });
    this.stateRestoreService.getState(this.constructor.name).subscribe(
      (state) => {
        if (state['gender']) {
          this.store.dispatch({
            'type': GENDER_UNCHECK_ALL
          });

          for (let gender of state['gender']) {
            if (gender === 'female' || gender === 'male') {
              this.store.dispatch({
                'type': GENDER_CHECK,
                'payload': gender
              });
            }
          }
        }
      }
    )

    this.genderState.subscribe(
      ([genderState, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

        this.male = genderState.male;
        this.female = genderState.female;
      }
    );
  }

  selectAll(): void {
    this.store.dispatch({
      'type': GENDER_CHECK_ALL,
    });
  }

  selectNone(): void {
    this.store.dispatch({
      'type': GENDER_UNCHECK_ALL,
    });
  }

  genderCheckValue(gender: string, value: boolean): void {
    if (gender === 'female' || gender === 'male') {
      this.store.dispatch({
        'type': value ? GENDER_CHECK : GENDER_UNCHECK,
        'payload': gender
      });
    }
  }

  getState() {
    return this.genderState.take(1).map(
      ([genderState, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid state"
        }
        return { gender: QueryData.trueFalseToStringArray(genderState) }
    });
  }
}
