import { Component, OnInit } from '@angular/core';
import { Phenotype } from '../phenotypes/phenotype';
import { DatasetService } from '../dataset/dataset.service';

@Component({
  selector: 'gpf-phenotypes',
  templateUrl: './phenotypes.component.html',
  styleUrls: ['./phenotypes.component.css']
})
export class PhenotypesComponent implements OnInit {

  phenotypes: Phenotype[];
  phenotypesCheck: boolean[];

  constructor(
    private datasetService: DatasetService
  ) { }

  ngOnInit() {
    this.datasetService.getPhenotypes(this.datasetService.selectedDatasetId)
      .then(pheno => {
        this.phenotypes = pheno;
        this.phenotypesCheck = new Array<boolean>(this.phenotypes.length);
        this.selectAll();
      });
  }


  selectAll(): void {
    if (this.phenotypes) {
      for (let i = 0; i < this.phenotypesCheck.length; i++) {
        this.phenotypesCheck[i] = true;
      }
    }
  }

  selectNone(): void {
    if (this.phenotypes) {
      for (let i = 0; i < this.phenotypesCheck.length; i++) {
        this.phenotypesCheck[i] = false;
      }
    }
  }

  getSelectedPhenotypes(): Set<string> {
    let selectedPhenotypes: Set<string> = new Set<string>();
    if (this.phenotypes) {
      for (let i = 0; i < this.phenotypesCheck.length; i++) {
        if (this.phenotypesCheck[i]) {
          selectedPhenotypes.add(this.phenotypes[i].id);
        }
      }
    }
    return selectedPhenotypes;
  }

}
