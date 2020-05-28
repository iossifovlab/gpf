import { Component, OnInit } from '@angular/core';
import { GeneService } from 'app/gene-draw/gene.service';
import { Gene } from 'app/gene-draw/gene';

@Component({
  selector: 'gpf-gene-view-component',
  templateUrl: './gene-view.component.html',
  styleUrls: ['./gene-view.component.css']
})
export class GeneViewComponent implements OnInit {
  selectedGene: Gene;
  geneSymbol: string;

  constructor(
    private geneService: GeneService
  ) {}

  ngOnInit() {
  }

  submitGeneRequest() {
    this.geneService.getGene(this.geneSymbol.toUpperCase().trim()).subscribe((gene) => {
      this.selectedGene = gene;
    });
  }
}
