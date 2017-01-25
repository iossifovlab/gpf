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

  COLUMN_HEADINGS = {
    FAMILY: "family",
    VARIANT: "variant",
    GENOTYPE: "genotype",
    EFFECT: "effect",
    ALLELE: "allele freq",
    RACES: "races",
    IQ: "Proband IQ"

  };
  COLUMN_SUBHEADINGS = {
    FAMILY_ID: "id",
    STDY: "stdy",
    LOC: "loc",
    VAR: "var",
    CH: "ch",
    PAR: "par",
    TYPE: "type",
    GENE: "gene",
    SSC: "SSC",
    EVS: "EVS",
    E65: "E65",
    MOM: "mom",
    DAD: "dad",
    VIQ: "vIQ",
    NVIQ: "NvIQ"
  };


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
