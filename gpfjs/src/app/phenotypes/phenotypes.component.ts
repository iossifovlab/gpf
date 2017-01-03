import { Component, OnInit } from '@angular/core';
import { Phenotype } from '../dataset/dataset';
import { DatasetService } from '../dataset/dataset.service';

@Component({
  selector: 'gpf-phenotypes',
  templateUrl: './phenotypes.component.html',
  styleUrls: ['./phenotypes.component.css']
})
export class PhenotypesComponent implements OnInit {

  phenotypes: Phenotype[];

  constructor(
    private datasetService: DatasetService
  ) { }

  ngOnInit() {
    this.datasetService.getPhenotypes(this.datasetService.selectedDatasetId)
      .then(pheno => {
        this.phenotypes = pheno;
      });
  }

}
