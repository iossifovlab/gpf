import { Component, Input, OnInit } from '@angular/core';

import { Chromosome } from '../chromosome-service/chromosome';
import { GenotypePreview } from '../genotype-preview-model/genotype-preview';

import * as _ from 'lodash';

interface ColorsMap {
  [gieStain: string]: string;
}

const COLORS: ColorsMap = {
  'acen' : '#8B2323',
  'gneg' : '#FFF',
  'gpos100' : '#000',
  'gpos25' : '##E5E5E5',
  'gpos50' : '#B3B3B3',
  'gpos75' : '#666',
  'gvar' : '#FFF',
  'stalk' : '#CD3333',
};

const GENOME_BROWSER: string = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr";

class ChromosomeBandComponent {
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  tooltip: string;
}

class GenotypeVariantComponent {
  x: number;
  color: string;
  proband: boolean;
  stackIndex: number;
  genes: string;
  location: string;
  genomeBrowserUrl: string;
}

@Component({
  selector: 'gpf-chromosome',
  templateUrl: './chromosome.component.html',
  styleUrls: ['./chromosome.component.css']
})
export class ChromosomeComponent implements OnInit {

  @Input()
  chromosome: Chromosome;

  @Input()
  genotypePreviews: GenotypePreview[];

  @Input()
  width: number;

  @Input()
  referenceLargestLength: number;

  @Input()
  centromerePosition: number;

  chromosomeHeight: number = 15;

  @Input()
  starWidth: number = 9.5;

  baseStarWidth: number = 9.5;

  nameWidth: number = 30;

  scale: number;
  startingPoint: number;
  leftWidth: number;
  rightWidth: number;
  leftBands: ChromosomeBandComponent[] = [];
  rightBands: ChromosomeBandComponent[] = [];
  variants: GenotypeVariantComponent[] = [];
  svgHeight: number;
  svgWidth: number;
  baseStarPathDescription: string;
  maxTopStackIndex: number = 1;
  maxBottomStackIndex: number = 1;
  maxStackIndex: number = 1;

  constructor() { }

  ngOnInit() {
    let starScale: number = this.starWidth / this.baseStarWidth;;

    this.baseStarPathDescription = `l ${1.64 * starScale} ${3.2 * starScale}
                                l ${3.2 * starScale} ${0.4 * starScale}
                                l ${-2.24 * starScale} ${2.24 * starScale}
                                l ${1.2 * starScale} ${4 * starScale}
                                l ${-3.6 * starScale} ${-2 * starScale}
                                l ${-3.6 * starScale} ${2 * starScale}
                                l ${1.2 * starScale} ${-4 * starScale}
                                l ${-2.4 * starScale} ${-2.3 * starScale}
                                l ${3.44 * starScale} ${-0.3 * starScale}`;


    this.svgWidth = this.width - this.nameWidth;
    this.scale = (this.svgWidth - this.starWidth) / this.referenceLargestLength;
    this.leftWidth = this.chromosome.leftWidth() * this.scale;
    this.rightWidth = this.chromosome.rightWidth() * this.scale;
    this.startingPoint = this.centromerePosition * this.scale - this.leftWidth + this.starWidth / 2;

    this.genotypePreviews = _.sortBy(this.genotypePreviews, genotypePreview => +genotypePreview.location.split(':')[1]);

    if (this.genotypePreviews) {
      for (let genotypePreview of this.genotypePreviews) {
        let locationInChromosome: number = +genotypePreview.location.split(':')[1];
        let x: number = locationInChromosome * this.scale + this.startingPoint;
        let proband: boolean = genotypePreview.inChild.indexOf('prb') != -1;
        let male: boolean = genotypePreview.inChild[3] == 'M';
        let stackIndex;

        let stackIndexMap: Map<number, boolean> = new Map();
        for (let i = this.variants.length - 1; i >= 0; i--) {
          let variant = this.variants[i];
          if (variant.proband == proband) {
            if ((x - variant.x) < this.starWidth) {
              stackIndexMap[variant.stackIndex] = true;
            } else {
              break;
            }
          }
        }
        
        for (let i = 1; ; i++) {
          if (!stackIndexMap[i]) {
            stackIndex = i;
            break;
          }
        }

        this.maxStackIndex = this.maxStackIndex < stackIndex ? stackIndex : this.maxStackIndex;

        this.variants.push({
          x: x,
          color: male ? 'blue' : 'red',
          stackIndex: stackIndex,
          proband: proband,
          genes: genotypePreview.genes,
          location: genotypePreview.location,
          genomeBrowserUrl: `${GENOME_BROWSER}${this.chromosome.id}:${locationInChromosome}-${locationInChromosome}`
        });
      }
    }

    this.svgHeight = this.chromosomeHeight + this.starWidth * 2 * (this.maxStackIndex);

    for (let band of this.chromosome.bands) {
      let bandComponent: ChromosomeBandComponent = {
        x: this.startingPoint + band.start * this.scale,
        y: this.starWidth * this.maxStackIndex + 1,
        width: (band.end - band.start) * this.scale,
        height: this.chromosomeHeight - 2,
        color: COLORS[band.gieStain],
        tooltip: band.name
      };
      if (band.end <= this.chromosome.leftWidth()) {
        this.leftBands.push(bandComponent);
      } else {
        this.rightBands.push(bandComponent);
      }
    }
  }
}
