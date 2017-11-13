import { Gender } from './gender';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider } from '../query/query-state-provider';
import { QueryData } from '../query/query';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => GenderComponent)
  }]
})
export class GenderComponent extends QueryStateProvider implements OnInit {

  gender = new Gender();
  errors: string[];
  flashingAlert = false;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .subscribe((state) => {
        if (state['gender']) {
          this.selectNone();
          for (let gender of state['gender']) {
            if (gender === 'female' || gender === 'male') {
             this.gender[gender] = true;
            }
          }
        }
      });
  }

  selectAll() {
    this.gender.male = true;
    this.gender.female = true;
  }

  selectNone() {
    this.gender.male = false;
    this.gender.female = false;
  }

  genderCheckValue(gender: string, value: boolean): void {
    if (gender === 'female' || gender === 'male') {
      this.gender[gender] = value;
    }
  }

  getState() {
    return toValidationObservable(this.gender)
      .map(genderState => ({
        gender: QueryData.trueFalseToStringArray(genderState)
      }))
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);
        return Observable.throw(`${this.constructor.name}: invalid state`);
      });
  }
}
