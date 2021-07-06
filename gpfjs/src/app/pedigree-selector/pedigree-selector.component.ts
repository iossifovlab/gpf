import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { Observable } from 'rxjs';
import { Validate, validate } from 'class-validator';
import { PedigreeSelector } from '../datasets/datasets';
import { SetNotEmpty } from '../utils/set.validators';
import { Store, Select } from '@ngxs/store';
import { SetPedigreeSelector, PedigreeSelectorState, PedigreeSelectorModel } from './pedigree-selector.state';

@Component({
  selector: 'gpf-pedigree-selector',
  templateUrl: './pedigree-selector.component.html',
  styleUrls: ['./pedigree-selector.component.css'],
})
export class PedigreeSelectorComponent implements OnInit, OnChanges {
  @Input() pedigrees: PedigreeSelector[];
  selectedPedigree: PedigreeSelector = null;

  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selectedValues: Set<string> = new Set();

  @Select(PedigreeSelectorState) state$: Observable<PedigreeSelectorModel>;
  errors: Array<string> = [];

  constructor(private store: Store) { }

  ngOnChanges(changes: SimpleChanges) {
    if (!changes['pedigrees']) {
      return;
    }
    this.store.selectOnce(state => state.pedigreeSelectorState).subscribe(state => {
      // handle selected values input and/or restore state
      if (state.id && state.checkedValues.length) {
        this.selectedPedigree = this.pedigrees.filter(p => p.id === state.id)[0];
        this.selectedValues = new Set(state.checkedValues);
      } else {
        if (changes['pedigrees'].currentValue && changes['pedigrees'].currentValue.length !== 0) {
          this.selectPedigree(0);
        }
      }
    });
  }

  ngOnInit() {
    this.store.selectOnce(state => state.pedigreeSelectorState).subscribe(state => {
      // restore state
      this.selectedPedigree = this.pedigrees.filter(p => p.id === state.id)[0];
      this.selectedValues = new Set(state.checkedValues);
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  pedigreeSelectorSwitch(): string {
    if (!this.pedigrees || this.pedigrees.length === 0) {
      return;
    }
    if (this.pedigrees.length === 1) {
      return 'single';
    }
    return 'multi';
  }

  selectPedigreeClicked(index: number, event: any): void {
    event.preventDefault();
    this.selectPedigree(index);
  }

  selectPedigree(index: number): void {
    if (index >= 0 && index < this.pedigrees.length && this.selectedPedigree !== this.pedigrees[index]) {
      this.selectedPedigree = this.pedigrees[index];
      this.selectAll();
    }
  }

  selectAll() {
    this.selectedValues = new Set(this.selectedPedigree.domain.map(sv => sv.id));
    this.store.dispatch(new SetPedigreeSelector(this.selectedPedigree.id, this.selectedValues));
  }

  selectNone() {
    this.selectedValues = new Set();
    this.store.dispatch(new SetPedigreeSelector(this.selectedPedigree.id, this.selectedValues));
  }

  pedigreeCheckValue(pedigreeSelector: PedigreeSelector, value: boolean): void {
    if (value) {
      this.selectedValues.add(pedigreeSelector.id);
    } else {
      this.selectedValues.delete(pedigreeSelector.id);
    }
    this.store.dispatch(new SetPedigreeSelector(this.selectedPedigree.id, this.selectedValues));
  }
}
