import { Component, OnInit, forwardRef } from '@angular/core';
import { Dataset, PedigreeSelector, DatasetsState } from '../datasets/datasets';
import { PedigreeSelectorState } from './pedigree-selector';

import { Observable } from 'rxjs';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-pedigree-selector',
  templateUrl: './pedigree-selector.component.html',
  styleUrls: ['./pedigree-selector.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PedigreeSelectorComponent) }]
})
export class PedigreeSelectorComponent extends QueryStateProvider implements OnInit {
  selectedDataset: Dataset;
  pedigrees: PedigreeSelector[];
  datasetsState: Observable<DatasetsState>; // FIXME: load from datasets service...
  pedigreeState = new PedigreeSelectorState();

  errors: string[];
  private flashingAlert = false;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name).subscribe(
      (state) => {
        if (state['pedigreeSelector'] && state['pedigreeSelector']['id']) {
          for (let pedigree of  this.pedigrees) {
            if (pedigree.id === state['pedigreeSelector']['id']) {
              this.pedigreeState.pedigree = pedigree;
              this.pedigreeState.checkedValues =
                new Set(pedigree.domain.map(sv => sv.id));
            }
          }
        }
        if (state['pedigreeSelector'] && state['pedigreeSelector']['checkedValues']) {
          this.pedigreeState.checkedValues =
            new Set(state['pedigreeSelector']['checkedValues']);
        }
      }
    );
  }

  ngOnInit() {
    this.datasetsState.subscribe(
      (datasetsState) => {
        let dataset = datasetsState.selectedDataset;
        if (dataset) {
          this.selectedDataset = dataset;
          if (dataset.pedigreeSelectors && dataset.pedigreeSelectors.length > 0) {
            this.pedigrees = dataset.pedigreeSelectors;
            this.selectPedigree(0);
          }
          this.restoreStateSubscribe();
        }
      }
    );
  }


  pedigreeSelectorSwitch(): string {
    if (!this.selectedDataset) {
      return undefined;
    }
    if (!this.selectedDataset.pedigreeSelectors) {
      return undefined;
    }
    if (this.selectedDataset.pedigreeSelectors.length === 0) {
      return undefined;
    }
    if (!this.pedigreeState.pedigree || !this.pedigreeState.pedigree.domain) {
      return undefined;
    }
    if (this.selectedDataset.pedigreeSelectors.length === 1) {
      return 'single';
    }
    return 'multi';
  }

  selectPedigreeClicked(index: number, event): void {
    event.preventDefault();
    this.selectPedigree(index);
  }

  selectPedigree(index): void {
    if (index >= 0 && index < this.pedigrees.length) {
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
    return toValidationObservable(this.pedigreeState)
      .map(pedigreeState => ({
        pedigreeSelector: {
          id: pedigreeState.pedigree.id,
          checkedValues: pedigreeState.checkedValues
        }
      }))
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);
        return Observable.throw(`${this.constructor.name}: invalid state`);
      });
  }
}
