import { Component, OnInit } from '@angular/core';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene } from 'app/gene-view/gene';

@Component({
  selector: 'gpf-gene-browser-component',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css']
})
export class GeneBrowserComponent implements OnInit {
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
