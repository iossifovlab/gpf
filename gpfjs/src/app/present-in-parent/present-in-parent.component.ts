import {
  PresentInParentState, PRESENT_IN_PARENT_CHECK_ALL,
  PRESENT_IN_PARENT_UNCHECK_ALL, PRESENT_IN_PARENT_UNCHECK,
  PRESENT_IN_PARENT_CHECK, PRESENT_IN_PARENT_RANGE_START_CHANGE,
  PRESENT_IN_PARENT_RANGE_END_CHANGE, PRESENT_IN_PARENT_ULTRA_RARE_CHANGE
} from './present-in-parent';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-present-in-parent',
  templateUrl: './present-in-parent.component.html',
})
export class PresentInParentComponent implements OnInit {
  motherOnly: boolean;
  fatherOnly: boolean;
  motherFather: boolean;
  neither: boolean;

  rarityIntervalStartInternal: number;
  rarityIntervalEndInternal: number;
  ultraRare: boolean;

  rarityRadio: string;

  presentInParentState: Observable<PresentInParentState>;

  constructor(
    private store: Store<any>
  ) {

    this.presentInParentState = this.store.select('presentInParent');
  }

  ngOnInit() {
    this.presentInParentState.subscribe(
      presentInParentState => {
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
        this.rarityChangeValue(0, 100);
        break;
      default:
        console.log('unexpected rarity: ', rarity);
    }
  }

}
