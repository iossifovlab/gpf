import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider } from '../query/query-state-provider'
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import {
  FamilyIdsState, FAMILY_IDS_CHANGE, FAMILY_IDS_INIT
} from './family-ids';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => FamilyIdsComponent) }]
})
export class FamilyIdsComponent extends QueryStateProvider implements OnInit {
  flashingAlert = false;
  errors: string[];
  familyIdsState: Observable<[FamilyIdsState, boolean, ValidationError[]]>;
  familyIdsInternal: string;

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    super();
    this.familyIdsState = toObservableWithValidation(FamilyIdsState ,this.store.select('familyIds'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': FAMILY_IDS_INIT,
    });

    this.familyIdsState.subscribe(
      ([familyIdsState, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);
        this.familyIdsInternal = familyIdsState.familyIds;
      }
    );

    this.stateRestoreService.state.subscribe(
      (state) => {
        if (state['familyIds']) {
          this.store.dispatch({
            'type': FAMILY_IDS_CHANGE,
            'payload': state['familyIds'].join("\n")
          });
        }
      }
    )
  }

  set familyIds(regionsFilter: string) {
    this.store.dispatch({
      'type': FAMILY_IDS_CHANGE,
      'payload': regionsFilter
    });
  }

  get familyIds() {
    return this.familyIdsInternal;
  }

  getState() {
    return this.familyIdsState.take(1).map(
      ([familyIdsState, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)
          throw "invalid state"
        }

        let result = familyIdsState.familyIds
          .split(/[,\s]/)
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }

        return { familyIds: result }
    });
  }

}
