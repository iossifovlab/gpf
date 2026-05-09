import { ChangeDetectionStrategy, Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectPresentInParent, setPresentInParent } from './present-in-parent.state';
import { take } from 'rxjs';
import { cloneDeep } from 'lodash';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
  selector: 'gpf-present-in-parent',
  templateUrl: './present-in-parent.component.html',
  styleUrls: ['./present-in-parent.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false
})
export class PresentInParentComponent implements OnInit {
  public rarityIntervalStart = 0;

  public rarityIntervalEnd = 1;

  public presentInParentValues: Set<string> = new Set([
    'mother only', 'father only', 'mother and father', 'neither'
  ]);

  public selectedValues: Set<string> = new Set();

  public rarityTypes: Set<string> = new Set([
    'all', 'rare', 'ultraRare', 'interval'
  ]);
  public selectedRarityType = '';
  @Input() public hasDenovo = false;
  @Input() public hasZygosity: boolean;
  public errors: string[] = [];

  public constructor(protected store: Store) {}

  public ngOnInit(): void {
    this.store.select(selectPresentInParent).pipe(take(1)).subscribe(state => {
      // restore state
      this.selectedValues = new Set([...state.presentInParent]);
      this.selectedRarityType = state.rarity.rarityType;
      this.rarityIntervalStart = state.rarity.rarityIntervalStart;
      this.rarityIntervalEnd = state.rarity.rarityIntervalEnd;
      this.validateState();
    });
  }

  public updatePresentInParent(newValues: Set<string>): void {
    this.selectedValues = newValues;
    if (newValues.size === 0) {
      // restore default rarity types
      this.rarityIntervalEnd = 1;
      this.rarityIntervalStart = 0;
      this.selectedRarityType = 'ultraRare';
    } else if (this.selectedValues.size === 1 && this.selectedValues.has('neither')) {
      // 'neither' does not allow for selecting a rarity type
      this.selectedRarityType = '';
    } else if (this.selectedRarityType === '') {
      // otherwise, set 'ultraRare' as default rarity type
      this.selectedRarityType = 'ultraRare';
    }
    this.updateState();
  }

  public updateRarityIntervalStart(newValue: number): void {
    this.rarityIntervalStart = newValue;
    this.updateState();
  }

  public updateRarityIntervalEnd(newValue: number): void {
    this.rarityIntervalEnd = newValue;
    this.updateState();
  }

  public updateRarityType(newValue: string): void {
    this.selectedRarityType = newValue;
    this.rarityIntervalEnd = 1;
    this.rarityIntervalStart = 0;
    this.updateState();
  }

  public updateState(): void {
    this.validateState();
    this.store.dispatch(setPresentInParent({
      presentInParent: {
        presentInParent: [...this.selectedValues],
        rarity: {
          rarityType: this.selectedRarityType,
          rarityIntervalStart: this.rarityIntervalStart,
          rarityIntervalEnd: this.rarityIntervalEnd,
        }
      }
    }));
  }

  private validateState(): void {
    this.errors = [];
    if (!this.selectedValues.size) {
      this.errors.push('Select at least one.');
    }

    if (this.selectedRarityType === 'interval') {
      if (this.rarityIntervalStart < 0) {
        this.errors.push('rarityIntervalStart must not be less than 0');
      }
      if (this.rarityIntervalStart > 100) {
        this.errors.push('rarityIntervalStart must not be greater than 100');
      }
      if (this.rarityIntervalStart >= this.rarityIntervalEnd) {
        this.errors.push('rarityIntervalStart should be less than or equal to rarityIntervalEnd');
      }
      if (this.rarityIntervalEnd <= this.rarityIntervalStart) {
        this.errors.push('rarityIntervalEnd should be more than or equal to rarityIntervalStart');
      }
    }

    if (this.selectedRarityType === 'interval' || this.selectedRarityType === 'rare') {
      if (this.rarityIntervalEnd < 0) {
        this.errors.push('rarityIntervalEnd must not be less than 0');
      }
      if (this.rarityIntervalEnd > 100) {
        this.errors.push('rarityIntervalEnd must not be greater than 100');
      }
    }


    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'presentInParent', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'presentInParent'}));
    }
  }
}
