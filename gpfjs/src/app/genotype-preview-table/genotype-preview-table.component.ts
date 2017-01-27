import { Component, OnInit } from '@angular/core';
import { QueryService } from '../query/query.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';


@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css']
})
export class GenotypePreviewTableComponent implements OnInit {
  private genotypePreviewsArray: GenotypePreviewsArray

  constructor(
    private queryService: QueryService
  ) { }

  ngOnInit() {
    this.queryService.getGenotypePreviewByFilter()
    .then(genotypePreviewsArray => {
      this.genotypePreviewsArray = genotypePreviewsArray
    });
  }
}
