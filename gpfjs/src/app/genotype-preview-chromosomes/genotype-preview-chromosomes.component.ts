import { Component, OnInit, Input } from '@angular/core';

import { GenotypePreviewsArray } from '../genotype-preview-model/genotype-preview';
import { Chromosome } from '../chromosome-service/chromosome';
import { ChromosomeService } from '../chromosome-service/chromosome.service';

import * as _ from 'lodash';

@Component({
  selector: 'gpf-genotype-preview-chromosomes',
  templateUrl: './genotype-preview-chromosomes.component.html',
  styleUrls: ['./genotype-preview-chromosomes.component.css']
})
export class GenotypePreviewChromosomesComponent implements OnInit {

  @Input()
  width: number;

  largestLength: number;

  centromerePosition: number;

  @Input()
  genotypePreviewsArray: GenotypePreviewsArray;

  genotypePreviewsByChromosome: any;

  chromosomes: Chromosome[];

  constructor(private chromosomeService: ChromosomeService) { }

  ngOnInit() {

    this.genotypePreviewsByChromosome = _.groupBy(this.genotypePreviewsArray.genotypePreviews,
      genotypePreview => genotypePreview.location.split(':')[0]);

    this.chromosomeService.getChromosomes().then(chromosomes => {
      this.chromosomes = chromosomes;
      // TODO chromosomes 1 left part & 2 right part are the longest
      this.largestLength = this.chromosomes[0].leftWidth() + this.chromosomes[1].rightWidth();
      this.centromerePosition = this.chromosomes[0].centromerePosition;
    });
  }

}
