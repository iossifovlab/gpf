import {
  PresentInParentState, PRESENT_IN_PARENT_INIT, PRESENT_IN_PARENT_CHECK_ALL,
  PRESENT_IN_PARENT_UNCHECK_ALL, PRESENT_IN_PARENT_UNCHECK,
  PRESENT_IN_PARENT_CHECK, PRESENT_IN_PARENT_RANGE_START_CHANGE,
  PRESENT_IN_PARENT_RANGE_END_CHANGE, PRESENT_IN_PARENT_ULTRA_RARE_CHANGE
} from './present-in-parent';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'
import { QueryData, Rarity } from '../query/query'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-present-in-parent',
  templateUrl: './present-in-parent.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PresentInParentComponent) }]
})
export class PresentInParentComponent extends QueryStateProvider implements OnInit {
  motherOnly: boolean;
  fatherOnly: boolean;
  motherFather: boolean;
  neither: boolean;

  rarityIntervalStartInternal: number;
  rarityIntervalEndInternal: number;
  ultraRare: boolean;

  rarityRadio: string;

  presentInParentState: Observable<[PresentInParentState, boolean, ValidationError[]]>;

  private errors: string[];
  private flashingAlert = false;

  constructor(
    private store: Store<any>
  ) {
    super();
    this.presentInParentState = toObservableWithValidation(PresentInParentState, this.store.select('presentInParent'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': PRESENT_IN_PARENT_INIT,
    });

    this.presentInParentState.subscribe(
      ([presentInParentState, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

        this.motherOnly = presentInParentState.motherOnly;
        this.fatherOnly = presentInParentState.fatherOnly;
        this.motherFather = presentInParentState.motherFather;
        this.neither = presentInParentState.neither;

        this.rarityIntervalStartInternal = presentInParentState.rarityIntervalStart;
        this.rarityIntervalEndInternal = presentInParentState.rarityIntervalEnd;
        this.ultraRare = presentInParentState.ultraRare;
      }
    );
  }

  selectAll(): void {
    this.store.dispatch({
      'type': PRESENT_IN_PARENT_CHECK_ALL,
    });
  }

  selectNone(): void {
    this.store.dispatch({
      'type': PRESENT_IN_PARENT_UNCHECK_ALL,
    });
  }

  presentInChildCheckValue(key: string, value: boolean): void {
    if (key === 'motherOnly' || key === 'fatherOnly' || key === 'motherFather' || key === 'neither') {
      this.store.dispatch({
        'type': value ? PRESENT_IN_PARENT_CHECK : PRESENT_IN_PARENT_UNCHECK,
        'payload': key
      });
    }
  }

  rarityChangeValue(start: number, end: number) {
    this.ultraRareValueChange(false);
    this.rarityIntervalStart = start;
    this.rarityIntervalEnd = end;
  }

  set rarityIntervalStart(start: number) {
    this.store.dispatch({
      'type': PRESENT_IN_PARENT_RANGE_START_CHANGE,
      'payload': start
    });
  }

  get rarityIntervalStart() {
    return this.rarityIntervalStartInternal;
  }


  set rarityIntervalEnd(end: number) {
    this.store.dispatch({
      'type': PRESENT_IN_PARENT_RANGE_END_CHANGE,
      'payload': end
    });
  }

  get rarityIntervalEnd() {
    return this.rarityIntervalEndInternal;
  }

  ultraRareValueChange(ultraRare: boolean) {
    this.store.dispatch({
      'type': PRESENT_IN_PARENT_ULTRA_RARE_CHANGE,
      'payload': ultraRare
    });
  }

  rarityRadioChange(rarity: string): void {
    console.log('rarity radio changed: ', rarity);
    this.ultraRareValueChange(false);
    switch (rarity) {
      case 'all':
        this.rarityRadio = 'all';
        this.rarityChangeValue(0, 100);
        break;
      case 'rare':
        this.rarityRadio = 'rare';
        this.rarityChangeValue(0, 1);
        break;
      case 'interval':
        this.rarityRadio = 'interval';
        this.rarityChangeValue(0, 1);
        break;
      default:
        console.log('unexpected rarity: ', rarity);
    }
  }

  getState() {
    return this.presentInParentState.take(1).map(
      ([presentInParentState, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

           throw "invalid state"
        }

        let result = new Array<string>();
        if (presentInParentState.fatherOnly) {
          result.push('father only');
        }
        if (presentInParentState.motherOnly) {
          result.push('mother only');
        }
        if (presentInParentState.motherFather) {
          result.push('mother and father');
        }
        if (presentInParentState.neither) {
          result.push('neither');
        }

        let rarity: Rarity = {
          ultraRare: presentInParentState.ultraRare,
          minFreq: presentInParentState.rarityIntervalStart,
          maxFreq: presentInParentState.rarityIntervalEnd
        };
        if (rarity.ultraRare) {
          rarity.minFreq = null;
          rarity.maxFreq = null;
        } else {
          rarity.ultraRare = null;
          if (rarity.minFreq <= 0.0) {
            rarity.minFreq = null;
          }
          if (rarity.maxFreq >= 100.0) {
            rarity.maxFreq = null;
          }
        }

        return { presentInParent: result, rarity: rarity }
    });
  }
}
