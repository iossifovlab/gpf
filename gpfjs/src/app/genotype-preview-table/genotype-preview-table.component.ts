import { Component, OnInit } from '@angular/core';
import { QueryService } from '../query/query.service';

@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css']
})
export class GenotypePreviewTableComponent implements OnInit {
  constructor(
    private queryService: QueryService
  ) { }

  ngOnInit() {
    this.queryService.getGenotypePreviewByFilter()
    .then(genotypePreviewsArray => {

    });
  }
}
