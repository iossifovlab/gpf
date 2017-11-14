import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';

import { QueryStateCollector } from '../query/query-state-provider';
import { Dataset, PedigreeSelector } from '../datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';

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
  pedigrees: Observable<Array<PedigreeSelector>>;

  constructor(
    private datasetsService: DatasetsService
  ) {
    super();
    let selectedDataset$: Observable<Dataset> =
      this.datasetsService.getSelectedDataset().share();
    this.hasCNV = selectedDataset$.map(dataset => {
      if (!dataset) {
        return false;
      }
      return dataset.genotypeBrowser.hasCNV;
    });
    this.hasPedigreeSelector = selectedDataset$.map(dataset => {
      if (!dataset) {
        return false;
      }
      return dataset.genotypeBrowser.hasPedigreeSelector;
    });
    this.hasPresentInChild = selectedDataset$.map(dataset => {
      if (!dataset) {
        return false;
      }
      return dataset.genotypeBrowser.hasPresentInChild;
    });
    this.hasPresentInParent = selectedDataset$.map(dataset => {
      if (!dataset) {
        return false;
      }
      return dataset.genotypeBrowser.hasPresentInParent;
    });
    this.hasStudyTypes = selectedDataset$.map(dataset => {
      if (!dataset) {
        return false;
      }
      return dataset.genotypeBrowser.hasStudyTypes;
    });
    this.pedigrees = selectedDataset$.map(dataset => {
      if (!dataset) {
        return [];
      }
      return dataset.pedigreeSelectors;
    });
  }

  ngOnInit() {
  }

}
