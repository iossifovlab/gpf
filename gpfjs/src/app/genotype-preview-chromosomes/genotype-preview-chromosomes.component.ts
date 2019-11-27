import { Component, OnInit, OnChanges, SimpleChanges, Input } from '@angular/core';

import { GenotypePreview } from '../genotype-preview-model/genotype-preview';
import { Chromosome } from '../chromosome-service/chromosome';
import { ChromosomeService } from '../chromosome-service/chromosome.service';

import * as _ from 'lodash';

@Component({
  selector: 'gpf-genotype-preview-chromosomes',
  templateUrl: './genotype-preview-chromosomes.component.html',
  styleUrls: ['./genotype-preview-chromosomes.component.css']
})
export class GenotypePreviewChromosomesComponent implements OnInit, OnChanges {

  @Input()
  width: number;

  leftLargestLength: number;

  rightLargestLength: number;

  leftColumnWidth: number;

  rightColumnWidth: number;

  leftCentromerePosition: number;

  rightCentromerePosition: number;

  @Input()
  genotypePreviews: GenotypePreview[];

  chromosomes: Chromosome[];

  constructor(private chromosomeService: ChromosomeService) { }

  ngOnInit() {
    this.chromosomeService.getChromosomes().subscribe((chromosomes) => {
      this.chromosomes = chromosomes;
      // TODO chromosomes 1 left part & 2 right part are the longest
      this.leftLargestLength = this.chromosomes[0].leftWidth() + this.chromosomes[1].rightWidth();
      this.leftCentromerePosition = this.chromosomes[0].centromerePosition;
      this.rightLargestLength = this.chromosomes[22].leftWidth() + this.chromosomes[12].rightWidth();
      this.rightCentromerePosition = this.chromosomes[22].centromerePosition;
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.width) {
      this.leftColumnWidth = 2 * this.width / 3;
      this.rightColumnWidth = this.width / 3;
    }
  }

  get genotypePreviewsByChromosome() {
    if (this.genotypePreviews) {
      return _.groupBy(this.genotypePreviews,
        genotypePreview => genotypePreview.get('variant.location').split(':')[0]
      );
    } else {
      return null;
    }
  }
}
