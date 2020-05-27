import { Component, OnInit } from '@angular/core';
import { GeneService } from 'app/gene-draw/gene.service';
import { Gene } from 'app/gene-draw/gene';

@Component({
  selector: 'gpf-gene-view-component',
  templateUrl: './gene-view.component.html',
  styleUrls: ['./gene-view.component.css']
})
export class GeneViewComponent implements OnInit {
  gene: Gene;
  geneSymbol: string;
  previewGeneFlag = false;

  constructor(
    private geneService: GeneService
  ) {}

  ngOnInit() {
  }

  previewGene() {
    this.previewGeneFlag = true;

    this.geneSymbol = this.standardizeGeneSymbol(this.geneSymbol);
    this.geneService.getGene(this.geneSymbol).subscribe((gene) => {
      this.gene = gene;
    });
  }

  standardizeGeneSymbol(geneSymbolToConvert: string): string {
    return geneSymbolToConvert.toUpperCase().trim();
  }
}
