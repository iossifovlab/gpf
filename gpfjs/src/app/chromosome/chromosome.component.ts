import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { Chromosome } from '../chromosome-service/chromosome';
import { GenotypePreview } from '../genotype-preview-model/genotype-preview';

import * as _ from 'lodash';

interface ColorsMap {
  [id: number]: string;
}

const COLORS: ColorsMap = {
  1 : 'white',
  2 : '#E8E8E8',
  3 : '#E0E0E0',
  4 : '#D8D8D8', 
  5 : '#D0D0D0',
  6 : '#808080',
  7 : '#A0A0A0',
  8 : '#C7C7C7',
};

const GENOME_BROWSER: string = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr";

enum Figure {
  None = 0,
  Star,
  Square,
  Circle,
}

const FIGURES_EFFECTS: Map<Figure, Array<string>> = new Map([
  [Figure.Star, ['nonsense', 'frame-shift', 'splice-site']],
  [Figure.Square, ['missense', 'no-frame-shift', 'noStart', 'noEnd']],
  [Figure.Circle, ['synonymous', 'non-coding', 'intron', 'intergenic', '3"UTR', '5"UTR']]
]);

function getFigureByEffect(effect: string) : Figure {
  for (let key of Array.from(FIGURES_EFFECTS.keys())) {
    if (FIGURES_EFFECTS.get(key).indexOf(effect) != -1) {
      return key;
    }
  }
  return Figure.None;
}

class ChromosomeBandComponent {
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
}

class GenotypeVariantComponent {
  x: number;
  figure: Figure;
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
export class ChromosomeComponent implements OnChanges {

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
  variantSignWidth: number = 9.5;

  baseVariantSignWidth: number = 9.5;

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

  ngOnChanges(changes: SimpleChanges) {
    let starScale: number = this.variantSignWidth / this.baseVariantSignWidth;;

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
    this.scale = (this.svgWidth - this.variantSignWidth) / this.referenceLargestLength;
    this.leftWidth = this.chromosome.leftWidth() * this.scale;
    this.rightWidth = this.chromosome.rightWidth() * this.scale;
    this.startingPoint = this.centromerePosition * this.scale - this.leftWidth + this.variantSignWidth / 2;

    this.variants = [];
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
            if ((x - variant.x) < this.variantSignWidth) {
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
          figure: getFigureByEffect(genotypePreview.worstEffectType),
          color: male ? 'blue' : 'red',
          stackIndex: stackIndex,
          proband: proband,
          genes: genotypePreview.genes,
          location: genotypePreview.location,
          genomeBrowserUrl: `${GENOME_BROWSER}${this.chromosome.id}:${locationInChromosome}-${locationInChromosome}`
        });
      }
    }

    this.svgHeight = this.chromosomeHeight + this.variantSignWidth * 2 * (this.maxStackIndex);

    this.leftBands = [];
    this.rightBands = [];
    for (let band of this.chromosome.bands) {
      let bandComponent: ChromosomeBandComponent = {
        x: this.startingPoint + band.start * this.scale,
        y: this.variantSignWidth * this.maxStackIndex + 1,
        width: (band.end - band.start) * this.scale,
        height: this.chromosomeHeight - 2,
        color: COLORS[band.color]
      };
      if (band.end <= this.chromosome.leftWidth()) {
        this.leftBands.push(bandComponent);
      } else {
        this.rightBands.push(bandComponent);
      }
    }
  }
}
