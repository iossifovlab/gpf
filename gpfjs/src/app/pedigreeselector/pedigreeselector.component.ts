import { Component, OnInit } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { Dataset, PedigreeSelector } from '../dataset/dataset';

@Component({
  selector: 'gpf-pedigreeselector',
  templateUrl: './pedigreeselector.component.html',
  styleUrls: ['./pedigreeselector.component.css']
})
export class PedigreeSelectorComponent implements OnInit {
  selectedDataset: Dataset;
  selectedPedigree: PedigreeSelector;
  pedigrees: PedigreeSelector[];
  pedigreeCheck: boolean[];

  constructor(
    private datasetService: DatasetService,
  ) { }

  ngOnInit() {
    this.datasetService.selectedDataset.subscribe(
      dataset => {
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
