import { Component, Input, OnChanges, SimpleChanges, forwardRef } from '@angular/core';
import { PedigreeSelector } from '../datasets/datasets';
import { PedigreeSelectorState } from './pedigree-selector';

import { Observable } from 'rxjs';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-pedigree-selector',
  templateUrl: './pedigree-selector.component.html',
  styleUrls: ['./pedigree-selector.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PedigreeSelectorComponent)
  }]
})
export class PedigreeSelectorComponent extends QueryStateWithErrorsProvider implements OnChanges {
  @Input()
  pedigrees: PedigreeSelector[];

  pedigreeState = new PedigreeSelectorState();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['peopleGroup'] && state['peopleGroup']['id']) {
          for (const pedigree of  this.pedigrees) {
            if (pedigree.id === state['peopleGroup']['id']
                  && (!this.pedigreeState.pedigree || this.pedigreeState.pedigree.id !== pedigree.id)) {
              this.pedigreeState.pedigree = pedigree;
              this.pedigreeState.checkedValues =
                new Set(pedigree.domain.map(sv => sv.id));
            }
          }
        }
        if (state['peopleGroup'] && state['peopleGroup']['checkedValues']) {
          const checkedValues = new Set(state['peopleGroup']['checkedValues']);
          if (checkedValues.size !== this.pedigreeState.checkedValues.size ||
              Array.from(this.pedigreeState.checkedValues).filter(v => checkedValues.has(v)).length !== 0) {
            this.pedigreeState.checkedValues = checkedValues;
          }
        }
      });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!changes['pedigrees']) {
      return;
    }
    if (changes['pedigrees'].currentValue
        && changes['pedigrees'].currentValue.length !== 0) {
      this.selectPedigree(0);
      this.restoreStateSubscribe();
    }
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

  selectPedigreeClicked(index: number, event): void {
    event.preventDefault();
    this.selectPedigree(index);
  }

  selectPedigree(index): void {
    if (index >= 0 && index < this.pedigrees.length
        && this.pedigreeState.pedigree !== this.pedigrees[index]) {
      this.pedigreeState.pedigree = this.pedigrees[index];
      this.selectAll();
    }
  }

  selectAll() {
    this.pedigreeState.checkedValues = new Set(this.pedigreeState.pedigree.domain.map(sv => sv.id));
  }

  selectNone() {
    this.pedigreeState.checkedValues = new Set();
  }

  pedigreeCheckValue(pedigreeSelector: PedigreeSelector, value: boolean): void {
    if (value) {
      this.pedigreeState.checkedValues.add(pedigreeSelector.id);
    } else {
      this.pedigreeState.checkedValues.delete(pedigreeSelector.id);
    }
  }

  getState() {
    return this.validateAndGetState(this.pedigreeState)
      .map(pedigreeState => ({
        peopleGroup: {
          id: pedigreeState.pedigree.id,
          checkedValues: Array.from(pedigreeState.checkedValues)
        }
      }));
  }
}
