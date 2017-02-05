import { Component, OnInit } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { Dataset, PedigreeSelector, DatasetsState } from '../dataset/dataset';

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

  constructor(
    private store: Store<any>,
  ) {
    this.datasetsState = this.store.select('datasets');

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
    if (this.selectedDataset.pedigreeSelectors.length === 1) {
      return 'single';
    }
    return 'multi';
  }

  selectPedigree(index: number): void {
    if (index >= 0 && index < this.pedigrees.length) {
      this.selectedPedigree = this.pedigrees[index];
      this.pedigreeCheck = new Array<boolean>(this.selectedPedigree.domain.length);
      this.selectAll();
    }
  }

  selectAll(): void {
    for (let i = 0; i < this.pedigreeCheck.length; ++i) {
      this.pedigreeCheck[i] = true;
    }
  }

  selectNone(): void {
    for (let i = 0; i < this.pedigreeCheck.length; ++i) {
      this.pedigreeCheck[i] = false;
    }
  }
}
