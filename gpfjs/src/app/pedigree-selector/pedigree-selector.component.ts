import { Component, OnInit } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { Dataset, PedigreeSelector, DatasetsState } from '../dataset/dataset';
import {
  PedigreeSelectorState, PEDIGREE_SELECTOR_INIT,
  PEDIGREE_SELECTOR_SET_CHECKED_VALUES, PEDIGREE_SELECTOR_CHECK_VALUE,
  PEDIGREE_SELECTOR_UNCHECK_VALUE
} from './pedigree-selector'

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-pedigree-selector',
  templateUrl: './pedigree-selector.component.html',
  styleUrls: ['./pedigree-selector.component.css']
})
export class PedigreeSelectorComponent implements OnInit {
  selectedDataset: Dataset;
  selectedPedigree: PedigreeSelector;
  pedigrees: PedigreeSelector[];
  pedigreeCheck: boolean[];
  datasetsState: Observable<DatasetsState>;
  pedigreeState: Observable<PedigreeSelectorState>;

  constructor(
    private store: Store<any>,
  ) {
    this.datasetsState = this.store.select('datasets');
    this.pedigreeState = this.store.select('pedigreeSelector');

  }

  ngOnInit() {
    this.datasetsState.subscribe(
      datasetsState => {
        let dataset = datasetsState.selectedDataset;
        if (dataset) {
          this.selectedDataset = dataset;
          if (dataset.pedigreeSelectors && dataset.pedigreeSelectors.length > 0) {
            this.pedigrees = dataset.pedigreeSelectors;
            this.selectPedigree(0);
          }
        }
      }
    );
    this.pedigreeState.subscribe(
      pedigreeState => {
        if (!pedigreeState) {
          return;
        }
        this.selectedPedigree = pedigreeState.pedigree;
        if (!this.selectedPedigree) {
          return;
        }
        let checkedValues = pedigreeState.checkedValues;

        for (let i = 0; i < this.selectedPedigree.domain.length; ++i) {
          let pedigreeId = this.selectedPedigree.domain[i].id;
          if (checkedValues.indexOf(pedigreeId) !== -1) {
            this.pedigreeCheck[i] = true;
          } else {
            this.pedigreeCheck[i] = false;
          }
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
    if (!this.selectedPedigree || !this.selectedPedigree.domain) {
      return undefined;
    }
    if (this.selectedDataset.pedigreeSelectors.length === 1) {
      return 'single';
    }
    return 'multi';
  }

  selectPedigree(index: number): void {
    if (index >= 0 && index < this.pedigrees.length) {
      this.selectedPedigree = this.pedigrees[index];
      this.store.dispatch({
        'type': PEDIGREE_SELECTOR_INIT,
        'payload': this.selectedPedigree,
      });
      this.pedigreeCheck = new Array<boolean>(this.selectedPedigree.domain.length);
      this.selectAll();
    }
  }

  selectAll(): void {
    this.store.dispatch({
      'type': PEDIGREE_SELECTOR_SET_CHECKED_VALUES,
      'payload': this.selectedPedigree.domain.map(sv => sv.id),
    });
  }

  selectNone(): void {
    this.store.dispatch({
      'type': PEDIGREE_SELECTOR_SET_CHECKED_VALUES,
      'payload': [],
    });
  }

  pedigreeCheckValue(index: number, value: boolean): void {
    if (index < 0 || index > this.selectedPedigree.domain.length) {
      return;
    }

    this.store.dispatch({
      'type': value ? PEDIGREE_SELECTOR_CHECK_VALUE : PEDIGREE_SELECTOR_UNCHECK_VALUE,
      'payload': this.selectedPedigree.domain[index].id,

    });
  }
}
