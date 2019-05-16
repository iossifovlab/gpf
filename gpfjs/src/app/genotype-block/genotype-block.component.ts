import { Component, AfterViewInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';

import { QueryStateCollector } from '../query/query-state-provider';
import { Dataset, PedigreeSelector, PresentInRole } from '../datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => GenotypeBlockComponent) }]
})
export class GenotypeBlockComponent extends QueryStateCollector implements AfterViewInit {
  hasCNV: Observable<boolean>;
  hasComplex: Observable<boolean>;
  hasPedigreeSelector: Observable<boolean>;
  hasPresentInChild: Observable<boolean>;
  hasPresentInParent: Observable<boolean>;
  hasPresentInRole: Observable<boolean>;
  hasStudyTypes: Observable<boolean>;
  pedigrees: Observable<Array<PedigreeSelector>>;
  presentInRole: Observable<Array<PresentInRole>>;
  selectedDataset$: Observable<Dataset>;
  rolesFilterOptions: Observable<Array<string>>;

  constructor(
    private datasetsService: DatasetsService
  ) {
    super();
  }

  ngAfterViewInit() {
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
    const selectedDataset$ = this.selectedDataset$;
    this.hasCNV = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasCNV;
    });
    this.hasComplex = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasComplex;
    });
    this.hasPedigreeSelector = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasPedigreeSelector;
    });
    this.hasPresentInChild = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasPresentInChild;
    });
    this.hasPresentInParent = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasPresentInParent;
    });
    this.hasPresentInRole = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasPresentInRole;
    });
    this.hasStudyTypes = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return false;
      }
      return dataset.genotypeBrowserConfig.hasStudyTypes;
    });
    this.pedigrees = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return [];
      }
      return dataset.genotypeBrowserConfig.pedigreeSelectors;
    });
    this.presentInRole = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return [];
      }
      return dataset.genotypeBrowserConfig.presentInRole;
    });
    this.rolesFilterOptions = selectedDataset$.map(dataset => {
      if (!dataset || !dataset.genotypeBrowserConfig) {
        return [];
      }
      return dataset.genotypeBrowserConfig.rolesFilterOptions;
    });
  }

}
