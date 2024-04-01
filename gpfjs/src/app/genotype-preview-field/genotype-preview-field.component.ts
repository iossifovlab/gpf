import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { sprintf } from 'sprintf-js';

interface FullEffectDetails {
  familyId: string;
  location: string;
  effectDetails: EffectDetail[];
  geneEffects: GeneEffects[];
  areIncomplete: boolean;
}

interface EffectDetail {
  gene: string;
  transcript: string;
  effect: string;
  details: string;
}

interface GeneEffects {
  gene: string;
  effect: string;
}

@Component({
  selector: 'gpf-genotype-preview-field',
  templateUrl: './genotype-preview-field.component.html',
  styleUrls: ['./genotype-preview-field.component.css']
})
export class GenotypePreviewFieldComponent implements OnInit, OnChanges {
  @Input() public value;
  @Input() public field: string;
  @Input() public format: string;
  @Input() public genome: string;

  public formattedValue: string;
  // eslint-disable-next-line @typescript-eslint/naming-convention
  public UCSCLink: string;
  public fullEffectDetails: FullEffectDetails;
  public pedigreeMaxHeight = 75;

  public ngOnInit(): void {
    this.UCSCLink = this.getUCSCLink();
    if (this.field === 'full_effect_details') {
      this.formatEffectDetails();
    }
  }

  public ngOnChanges(): void {
    this.formattedValue = this.formatValue();
  }

  private formatEffectDetails(): void {
    if (this.value instanceof Array
      && typeof this.value[0] === 'string'
      && typeof this.value[1] === 'string'
      && typeof this.value[2] === 'string'
      && typeof this.value[3] === 'string'
    ) {
      this.fullEffectDetails = {
        familyId: '',
        location: '',
        effectDetails: [],
        geneEffects: [],
        areIncomplete: true
      };
      this.fullEffectDetails.familyId = this.value[0];
      this.fullEffectDetails.location = this.value[1];
      this.fullEffectDetails.effectDetails = this.value[2].split('|').map(detail => {
        const details = detail.split(':');
        return {
          gene: details[1],
          transcript: details[0],
          effect: details[2],
          details: details[3],
        };
      }).sort((e1, e2) => {
        if (e1.gene < e2.gene) {
          return -1;
        }
        if (e1.gene > e2.gene) {
          return 1;
        }
        return 0;
      });

      // Check if gene and effect columns are both empty
      for (const ed of this.fullEffectDetails.effectDetails) {
        // Equal only when both are 'None'
        if (ed.gene !== ed.effect) {
          this.fullEffectDetails.areIncomplete = false;
          break;
        }
      }

      this.fullEffectDetails.geneEffects = this.value[3].split('|').map(geneEffect => {
        const effect = geneEffect.split(':');
        return {
          gene: effect[0],
          effect: effect[1],
        };
      });
    }
  }

  private doFormat(format, value) {
    if (value === 'nan') {
      return value;
    }
    return sprintf(format, value);
  }

  public formatValue() {
    if (this.value) {
      if (this.format) {
        if (this.value.constructor === Array) {
          return this.value.map(x => x === '-' ? '-' : this.doFormat(this.format, x));
        }
        if (typeof this.value === 'string') {
          return this.value;
        }
        return this.doFormat(this.format, this.value);
      }
      return this.value;
    }
    return '';
  }

  public getUCSCLink(): string {
    let link: string;
    if (this.genome === 'hg19') {
      link = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr${this.value}`;
    } else if (this.genome === 'hg38') {
      link = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=${this.value}`;
    }
    return link;
  }
}
