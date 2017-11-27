import {
  PresentInParent, RARITY_ULTRARARE, RARITY_INTERVAL, RARITY_RARE, RARITY_ALL
} from './present-in-parent';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { QueryData, Rarity } from '../query/query';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-present-in-parent',
  templateUrl: './present-in-parent.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PresentInParentComponent) }]
})
export class PresentInParentComponent extends QueryStateWithErrorsProvider implements OnInit {
  ultraRare: boolean;

  rarityRadio: string;

  presentInParent = new PresentInParent();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  restoreCheckedState(state) {
    for (let key of state) {
      if (key === 'father only') {
        this.presentInParent.fatherOnly = true;
      }
      if (key === 'mother only') {
        this.presentInParent.motherOnly = true;
      }
      if (key === 'mother and father') {
        this.presentInParent.motherFather = true;
      }
      if (key === 'neither') {
        this.presentInParent.neither = true;
      }
    }
  }

  restoreRarity(state) {
    if (state['ultraRare']) {
      this.presentInParent.ultraRare = true;
      this.presentInParent.rarityType = RARITY_ULTRARARE;
    } else {
      this.presentInParent.ultraRare = false;

      if (state['minFreq']) {
        this.presentInParent.rarityIntervalStart = state['minFreq'];
      }

      if (state['maxFreq']) {
        this.presentInParent.rarityIntervalEnd = state['maxFreq'];
      }

      this.restoreRadioButtonState(state);
    }
  }

  restoreRadioButtonState(state) {
    this.setFrequenciesState(
      state['ultraRare'], state['minFreq'], state['maxFreq']);
  }

  setFrequenciesState(ultraRare, minFrequency, maxFrequency) {
    if (ultraRare) {
      this.ultraRareValueChange(true);
    } else {
      if (minFrequency && minFrequency > 0) {
        this.rarityTypeChange(RARITY_INTERVAL);
      } else {
        if (maxFrequency && maxFrequency < 100) {
          this.rarityTypeChange(RARITY_RARE);
        } else {
          this.rarityTypeChange(RARITY_ALL);
        }
      }
    }
  }

  restoreState() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['presentInParent'] && state['presentInParent']['presentInParent']) {
          this.restoreCheckedState(state['presentInParent']['presentInParent']);
        }

        if (state['presentInParent'] && state['presentInParent']['rarity']) {
          this.restoreRarity(state['presentInParent']['rarity']);
        }
      }
    );
  }

  ngOnInit() {
    this.restoreState();
  }

  selectAll(): void {
    this.presentInParent.fatherOnly = true;
    this.presentInParent.motherOnly = true;
    this.presentInParent.motherFather = true;
    this.presentInParent.neither = true;
  }

  selectNone(): void {
    this.presentInParent.fatherOnly = false;
    this.presentInParent.motherOnly = false;
    this.presentInParent.motherFather = false;
    this.presentInParent.neither = false;
  }

  presentInChildCheckValue(key: string, value: boolean): void {
    if (key === 'motherOnly' || key === 'fatherOnly' || key === 'motherFather' || key === 'neither') {
      this.presentInParent[key] = value;
    }
  }

  rarityChangeValue(start: number, end: number) {
    this.presentInParent.rarityIntervalStart = start;
    this.presentInParent.rarityIntervalEnd = end;
  }

  rarityTypeChange(rarityType: string) {
    this.presentInParent.rarityType = rarityType;
  }

  ultraRareValueChange(ultraRare: boolean) {
    this.presentInParent.ultraRare = ultraRare;
    if (ultraRare) {
      this.presentInParent.rarityType = RARITY_ULTRARARE;
    }
  }

  rarityRadioChange(rarity: string): void {
    this.ultraRareValueChange(false);
    switch (rarity) {
      case 'all':
        this.rarityTypeChange(RARITY_ALL);
        this.rarityChangeValue(0, 100);
        break;
      case 'rare':
        this.rarityTypeChange(RARITY_RARE);
        this.rarityChangeValue(0, 1);
        break;
      case 'interval':
        this.rarityTypeChange(RARITY_INTERVAL);
        this.rarityChangeValue(0, 1);
        break;
      default:
        console.log('unexpected rarity: ', rarity);
    }
  }

  getState() {
    return this.validateAndGetState(this.presentInParent)
      .map(presentInParent => {
        let result = new Array<string>();
        if (presentInParent.fatherOnly) {
          result.push('father only');
        }
        if (presentInParent.motherOnly) {
          result.push('mother only');
        }
        if (presentInParent.motherFather) {
          result.push('mother and father');
        }
        if (presentInParent.neither) {
          result.push('neither');
        }

        let rarity: Rarity = {
          ultraRare: presentInParent.ultraRare,
          minFreq: presentInParent.rarityIntervalStart,
          maxFreq: presentInParent.rarityIntervalEnd
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

        return {
          presentInParent: {
            presentInParent: result,
            rarity: rarity
          }
        };
      });
  }
}
