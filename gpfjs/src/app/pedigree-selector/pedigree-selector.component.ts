import { Component, Input, OnInit, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { Validate } from 'class-validator';
import { PersonSet, PersonSetCollection } from '../datasets/datasets';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngxs/store';
import { SetPedigreeSelector, PedigreeSelectorState, PedigreeSelectorModel } from './pedigree-selector.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-pedigree-selector',
  templateUrl: './pedigree-selector.component.html',
  styleUrls: ['./pedigree-selector.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PedigreeSelectorComponent extends StatefulComponent implements OnInit, OnChanges {
  @Input() public collections: PersonSetCollection[];
  public selectedCollection: PersonSetCollection = null;

  @Validate(SetNotEmpty, {
    message: 'Select at least one.'
  })
  public selectedValues: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, PedigreeSelectorState, 'pedigreeSelector');
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (!changes['collections']) {
      return;
    }
    this.store.selectOnce(state => state.pedigreeSelectorState as PedigreeSelectorModel).subscribe(state => {
      // handle selected values input and/or restore state
      if (state.id && state.checkedValues.length) {
        this.selectedCollection = this.collections.filter(p => p.id === state.id)[0];
        this.selectedValues = new Set(state.checkedValues);
      } else if (changes['collections'].currentValue && changes['collections'].currentValue.length !== 0) {
        this.selectPedigree(0);
      }
    });
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.selectOnce(state => state.pedigreeSelectorState).subscribe(state => {
      // restore state
      this.selectedCollection = this.collections.filter(p => p.id === state.id)[0];
      this.selectedValues = new Set(state.checkedValues);
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
    this.selectedValues = new Set(this.selectedCollection.domain.map(sv => sv.id));
    this.store.dispatch(new SetPedigreeSelector(this.selectedCollection.id, this.selectedValues));
  }

  public selectNone(): void {
    this.selectedValues = new Set();
    this.store.dispatch(new SetPedigreeSelector(this.selectedCollection.id, this.selectedValues));
  }

  public pedigreeCheckValue(pedigreeSelector: PersonSet, value: boolean): void {
    if (value) {
      this.selectedValues.add(pedigreeSelector.id);
    } else {
      this.selectedValues.delete(pedigreeSelector.id);
    }
    this.store.dispatch(new SetPedigreeSelector(this.selectedCollection.id, this.selectedValues));
  }
}
