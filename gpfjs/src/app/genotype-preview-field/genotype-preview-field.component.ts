import { Component, OnInit, Input } from '@angular/core';

import { sprintf } from 'sprintf-js';

@Component({
  selector: 'gpf-genotype-preview-field',
  templateUrl: './genotype-preview-field.component.html',
  styleUrls: ['./genotype-preview-field.component.css']
})
export class GenotypePreviewFieldComponent implements OnInit {

  @Input()
  value: any;

  @Input()
  field: string;

  @Input()
  format: string;

  constructor() { }

  ngOnInit() {
  }

  formattedValue() {
      if (this.value) {
        if (this.format) {
          if (this.value.constructor === Array) {
            return this.value.map(x => sprintf(this.format, x));
          }
          return sprintf(this.format, this.value);
        }
        return this.value;
      }
      return "";
  }
}
