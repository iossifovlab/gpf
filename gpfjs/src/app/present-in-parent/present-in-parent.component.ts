import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngxs/store';
import { Validate, ValidateIf, Min, Max } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { SetPresentInParentValues, PresentInParentState } from './present-in-parent.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-present-in-parent',
  templateUrl: './present-in-parent.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PresentInParentComponent extends StatefulComponent implements OnInit {
  @ValidateIf(o => o.selectedRarityType !== 'ultraRare' && o.rarityIntervalStart !== null)
  @Min(0) @Max(100)
  @IsLessThanOrEqual('rarityIntervalEnd')
  public rarityIntervalStart = 0;

  @ValidateIf(o => o.selectedRarityType !== 'ultraRare')
  @Min(0) @Max(100)
  @IsMoreThanOrEqual('rarityIntervalStart')
  public rarityIntervalEnd = 1;

  public presentInParentValues: Set<string> = new Set([
    'mother only', 'father only', 'mother and father', 'neither'
  ]);

  @Validate(SetNotEmpty, { message: 'Select at least one.' })
  public selectedValues: Set<string> = new Set();

  public rarityTypes: Set<string> = new Set([
    'ultraRare', 'interval', 'rare', 'all'
  ]);
  public selectedRarityType = '';

  public constructor(protected store: Store) {
    super(store, PresentInParentState, 'presentInParent');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.selectOnce(PresentInParentState).subscribe(state => {
      // restore state
      this.selectedValues = new Set([...state.presentInParent]);
      this.selectedRarityType = state.rarityType;
      this.rarityIntervalStart = state.rarityIntervalStart;
      this.rarityIntervalEnd = state.rarityIntervalEnd;
      this.updateState();
    });
  }

  public contains(string, value) {
    return string.has(value);
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
    this.store.dispatch(new SetPresentInParentValues(
      this.selectedValues, this.selectedRarityType,
      this.rarityIntervalStart, this.rarityIntervalEnd
    ));
  }
}
