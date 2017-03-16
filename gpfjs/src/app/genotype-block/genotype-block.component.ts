import { DatasetsState } from '../datasets/datasets';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => GenotypeBlockComponent) }]
})
export class GenotypeBlockComponent extends QueryStateCollector implements OnInit {
  hasCNV: Observable<boolean>;
  hasPedigreeSelector: Observable<boolean>;
  hasPresentInChild: Observable<boolean>;
  hasPresentInParent: Observable<boolean>;
  hasStudyTypes: Observable<boolean>;

  constructor(
    private store: Store<any>
  ) {
    super();
    let datasetsState: Observable<DatasetsState> = this.store.select('datasets');
    this.hasCNV = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasCNV;
    });
    this.hasPedigreeSelector = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasPedigreeSelector;
    });
    this.hasPresentInChild = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasPresentInChild;
    });
    this.hasPresentInParent = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasPresentInParent;
    });
    this.hasStudyTypes = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasStudyTypes;
    });
  }

  ngOnInit() {
  }

}
