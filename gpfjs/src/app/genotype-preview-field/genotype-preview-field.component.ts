import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { sprintf } from 'sprintf-js';

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
  public showEffectDetails = false;
  public pedigreeMaxHeight = 75;

  public ngOnInit(): void {
    this.UCSCLink = this.getUCSCLink();
    if (this.field === 'effect_details') {
      this.formatEffectDetails();
    }
  }

  public ngOnChanges(): void {
    this.formattedValue = this.formatValue();
  }

  private formatEffectDetails(): void {
    if (this.value instanceof Array && typeof this.value[0] === 'string') {
      let formattedDetails = this.value[0];
      formattedDetails = formattedDetails.replaceAll('|', '\n');
      formattedDetails = formattedDetails.replaceAll(':', ': ');
      this.value[0] = formattedDetails;
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
