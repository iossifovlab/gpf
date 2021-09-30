import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { Validate } from 'class-validator';
import { PersonSetCollection } from '../datasets/datasets';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngxs/store';
import { SetPedigreeSelector, PedigreeSelectorState } from './pedigree-selector.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-pedigree-selector',
  templateUrl: './pedigree-selector.component.html',
  styleUrls: ['./pedigree-selector.component.css'],
})
export class PedigreeSelectorComponent extends StatefulComponent implements OnInit, OnChanges {
  @Input() collections: PersonSetCollection[];
  selectedCollection: PersonSetCollection = null;

  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selectedValues: Set<string> = new Set();

  constructor(protected store: Store) {
    super(store, PedigreeSelectorState, 'pedigreeSelector');
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!changes['collections']) {
      return;
    }
    this.store.selectOnce(state => state.pedigreeSelectorState).subscribe(state => {
      // handle selected values input and/or restore state
      if (state.id && state.checkedValues.length) {
        this.selectedCollection = this.collections.filter(p => p.id === state.id)[0];
        this.selectedValues = new Set(state.checkedValues);
      } else {
        if (changes['collections'].currentValue && changes['collections'].currentValue.length !== 0) {
          this.selectPedigree(0);
        }
      }
    });
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(state => state.pedigreeSelectorState).subscribe(state => {
      // restore state
      this.selectedCollection = this.collections.filter(p => p.id === state.id)[0];
      this.selectedValues = new Set(state.checkedValues);
    });
  }

  pedigreeSelectorSwitch(): string {
    if (!this.collections || this.collections.length === 0) {
      return;
    }
    if (this.collections.length === 1) {
      return 'single';
    }
    return 'multi';
  }

  selectPedigreeClicked(index: number, event: any): void {
    event.preventDefault();
    this.selectPedigree(index);
  }

  selectPedigree(index: number): void {
    if (index >= 0 && index < this.collections.length && this.selectedCollection !== this.collections[index]) {
      this.selectedCollection = this.collections[index];
      this.selectAll();
    }
  }

  selectAll() {
    this.selectedValues = new Set(this.selectedCollection.domain.map(sv => sv.id));
    this.store.dispatch(new SetPedigreeSelector(this.selectedCollection.id, this.selectedValues));
  }

  selectNone() {
    this.selectedValues = new Set();
    this.store.dispatch(new SetPedigreeSelector(this.selectedCollection.id, this.selectedValues));
  }

  pedigreeCheckValue(pedigreeSelector: PersonSetCollection, value: boolean): void {
    if (value) {
      this.selectedValues.add(pedigreeSelector.id);
    } else {
      this.selectedValues.delete(pedigreeSelector.id);
    }
    this.store.dispatch(new SetPedigreeSelector(this.selectedCollection.id, this.selectedValues));
  }
}
