import { Component, OnInit, Input } from '@angular/core';

import { GenotypePreviewsArray } from '../genotype-preview-model/genotype-preview';
import { Chromosome } from '../chromosome-service/chromosome';
import { ChromosomeService } from '../chromosome-service/chromosome.service';

@Component({
  selector: 'gpf-genotype-preview-chromosomes',
  templateUrl: './genotype-preview-chromosomes.component.html',
  styleUrls: ['./genotype-preview-chromosomes.component.css']
})
export class GenotypePreviewChromosomesComponent implements OnInit {

  @Input()
  width: number;

  scale: number;

  centromerePosition: number;

  @Input()
  genotypePreviewsArray: GenotypePreviewsArray;

  chromosomes: Chromosome[];

  constructor(private chromosomeService: ChromosomeService) { }

  ngOnInit() {
    this.chromosomeService.getChromosomes().then(chromosomes => {
      this.chromosomes = chromosomes;
      // TODO chromosomes 1 left part & 2 right part are the longest
      this.scale = this.width / (this.chromosomes[0].leftWidth() + this.chromosomes[1].rightWidth());
      this.centromerePosition = this.chromosomes[0].centromerePosition * this.scale;
    });
  }

}
