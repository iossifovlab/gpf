import { Component, OnInit, forwardRef } from '@angular/core';
import { validate } from 'class-validator';
import { QueryStateProvider } from '../query/query-state-provider';
import { Observable } from 'rxjs';
import { FamilyIds } from './family-ids';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => FamilyIdsComponent) }]
})
export class FamilyIdsComponent extends QueryStateProvider implements OnInit {
  flashingAlert = false;
  errors: string[];

  familyIds = new FamilyIds();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService
      .getState(this.constructor.name)
      .take(1)
      .subscribe(
      (state) => {
        if (state['familyIds']) {
          this.familyIds.familyIds = state['familyIds'].join('\n');
        }
      }
    );
  }

  getState() {
    return toValidationObservable(this.familyIds).map(familyIds => {
        let result = familyIds.familyIds
          .split(/[,\s]/)
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }

        return { familyIds: result };
    })
    .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);
        return Observable.throw(`${this.constructor.name}: invalid state`);
    });
  }

}
