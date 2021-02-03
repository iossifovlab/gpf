import { Component, Input, OnChanges } from '@angular/core';

import { sprintf } from 'sprintf-js';

@Component({
  selector: 'gpf-genotype-preview-field',
  templateUrl: './genotype-preview-field.component.html',
  styleUrls: ['./genotype-preview-field.component.css']
})
export class GenotypePreviewFieldComponent implements OnChanges {

  @Input()
  value: any;

  @Input()
  field: string;

  @Input()
  format: string;

  formattedValue: string;

  constructor() { }

  ngOnChanges() {
    this.formattedValue = this.formatValue();
  }

  formatValue() {
      if (this.value) {
        if (this.format) {
          if (this.value.constructor === Array) {
            return this.value.map(x => sprintf(this.format, x));
          }
          if (typeof this.value === 'string') {
            return this.value;
          }
          return sprintf(this.format, this.value);
        }
        return this.value;
      }
      return '';
  }

  getUCSCLink(): string {
    let link: string;

    if (this.value.substring(0, 3) === 'chr') {
      link = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=${this.value}`;
    } else {
      link = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr${this.value}`;
    }

    return link;
  }
}
