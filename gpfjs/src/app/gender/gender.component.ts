import { Gender } from './gender';
import { Component, OnInit, forwardRef } from '@angular/core';

import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
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
export class GenderComponent extends QueryStateWithErrorsProvider implements OnInit {

  gender = new Gender();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe((state) => {
        if (state['gender']) {
          this.selectNone();
          for (const gender of state['gender']) {
            if (gender === 'female' || gender === 'male' || gender === 'unspecified') {
             this.gender[gender] = true;
            }
          }
        }
      });
  }

  selectAll() {
    this.gender.male = true;
    this.gender.female = true;
    this.gender.unspecified = true;
  }

  selectNone() {
    this.gender.male = false;
    this.gender.female = false;
    this.gender.unspecified = false;
  }

  genderCheckValue(gender: string, value: boolean): void {
    if (gender === 'female' || gender === 'male' || gender === 'unspecified') {
      this.gender[gender] = value;
    }
  }

  getState() {
    return this.validateAndGetState(this.gender)
      .map(genderState => ({
        gender: QueryData.trueFalseToStringArray(genderState)
      }));
  }
}
