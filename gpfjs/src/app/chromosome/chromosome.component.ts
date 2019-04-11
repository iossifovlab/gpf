import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

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
  'M' : 'blue',
  'F' : 'red',
  'U' : 'green'
};

const GENOME_BROWSER = 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr';

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

function getFigureByEffect(effect: string): Figure {
  for (const key of Array.from(FIGURES_EFFECTS.keys())) {
    if (FIGURES_EFFECTS.get(key).indexOf(effect) !== -1) {
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
  tooltip: string;
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

  chromosomeHeight = 15;

  @Input()
  variantSignWidth = 9.5;

  baseVariantSignWidth = 9.5;

  nameWidth = 30;

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
  maxTopStackIndex = 1;
  maxBottomStackIndex = 1;
  maxStackIndex = 1;

  constructor() { }

  ngOnChanges(changes: SimpleChanges) {
    const starScale: number = this.variantSignWidth / this.baseVariantSignWidth;

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
    this.genotypePreviews = _.sortBy(this.genotypePreviews,
      (genotypePreview: GenotypePreview) => +genotypePreview.get('location').split(':')[1]);

    if (this.genotypePreviews) {
      for (const genotypePreview of this.genotypePreviews) {
        const locationInChromosome: number = +genotypePreview.get('location').split(':')[1];
        const x: number = locationInChromosome * this.scale + this.startingPoint;
        const proband: boolean = genotypePreview.get('inChS').indexOf('prb') !== -1;
        const sex: string = genotypePreview.get('inChS')[3];
        let stackIndex;

        const stackIndexMap: Map<number, boolean> = new Map();
        for (let i = this.variants.length - 1; i >= 0; i--) {
          const variant = this.variants[i];
          if (variant.proband === proband) {
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
          figure: getFigureByEffect(genotypePreview.get('effectType')),
          color: COLORS[sex],
          stackIndex: stackIndex,
          proband: proband,
          genes: genotypePreview.get('genes'),
          location: genotypePreview.get('location'),
          genomeBrowserUrl: `${GENOME_BROWSER}${this.chromosome.id}:${locationInChromosome}-${locationInChromosome}`
        });
      }
    }

    this.svgHeight = this.chromosomeHeight + this.variantSignWidth * 2 * (this.maxStackIndex);

    this.leftBands = [];
    this.rightBands = [];
    for (const band of this.chromosome.bands) {
      const bandComponent: ChromosomeBandComponent = {
        x: this.startingPoint + band.start * this.scale,
        y: this.variantSignWidth * this.maxStackIndex + 1,
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
