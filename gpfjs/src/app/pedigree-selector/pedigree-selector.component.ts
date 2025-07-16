import { Component, Input, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { Validate } from 'class-validator';
import { PersonSet, PersonSetCollection } from '../datasets/datasets';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngrx/store';
import { ComponentValidator } from 'app/common/component-validator';
import { selectPedigreeSelector, setPedigreeSelector } from './pedigree-selector.state';
import { take } from 'rxjs';

@Component({
    selector: 'gpf-pedigree-selector',
    templateUrl: './pedigree-selector.component.html',
    styleUrls: ['./pedigree-selector.component.css'],
    changeDetection: ChangeDetectionStrategy.OnPush,
    standalone: false
})
export class PedigreeSelectorComponent extends ComponentValidator implements OnInit {
  @Input() public collections: PersonSetCollection[];
  @Input() public hasZygosity: boolean;
  public selectedCollection: PersonSetCollection = null;

  @Validate(SetNotEmpty, {
    message: 'Select at least one.'
  })
  public selectedValues: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, 'pedigreeSelector', selectPedigreeSelector);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.select(selectPedigreeSelector).pipe(take(1)).subscribe(pedigreeSelectorState => {
      if (!pedigreeSelectorState) {
        this.selectAll();
        return;
      }

      if (pedigreeSelectorState.id && pedigreeSelectorState.checkedValues.length) {
        this.selectedCollection = this.collections.filter(p => p.id === pedigreeSelectorState.id)[0];
        this.selectedValues = new Set(pedigreeSelectorState.checkedValues);
        this.dispatchState();
      }
    });
  }

  public pedigreeSelectorSwitch(): string {
    if (!this.collections || this.collections.length === 0) {
      return;
    }
    if (this.collections.length === 1) {
      return 'single';
    }
    return 'multi';
  }

  public selectPedigreeClicked(index: number, event: any): void {
    event.preventDefault();
    this.selectPedigree(index);
  }

  public selectPedigree(index: number): void {
    if (index >= 0 && index < this.collections.length && this.selectedCollection !== this.collections[index]) {
      this.selectedCollection = this.collections[index];
      this.selectAll();
    }
  }

  public selectAll(): void {
    if (this.selectedCollection === null) {
      this.selectedCollection = this.collections[0];
    }

    this.selectedValues = new Set(this.selectedCollection.domain.map(sv => sv.id));
    this.dispatchState();
  }

  public selectNone(): void {
    this.selectedValues = new Set();
    this.dispatchState();
  }

  public pedigreeCheckValue(pedigreeSelector: PersonSet, value: boolean): void {
    if (value) {
      this.selectedValues.add(pedigreeSelector.id);
    } else {
      this.selectedValues.delete(pedigreeSelector.id);
    }
    this.dispatchState();
  }

  public dispatchState(): void {
    this.store.dispatch(setPedigreeSelector({
      pedigreeSelector: {
        id: this.selectedCollection.id,
        checkedValues: [...this.selectedValues]
      }
    }));
  }
}
