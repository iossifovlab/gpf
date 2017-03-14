import {
  GenderState, GENDER_CHECK_ALL,
  GENDER_UNCHECK_ALL, GENDER_UNCHECK, GENDER_CHECK
} from './gender';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css']
})
export class GenderComponent implements OnInit {
  male: boolean = true;
  female: boolean = true;

  genderState: Observable<[GenderState, boolean, ValidationError[]]>;
  private errors: string[];

  constructor(
    private store: Store<any>
  ) {

    this.genderState = toObservableWithValidation(GenderState, this.store.select('gender'));
  }

  ngOnInit() {
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
}
