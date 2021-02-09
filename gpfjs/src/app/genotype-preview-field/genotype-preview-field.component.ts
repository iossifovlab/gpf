import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { sprintf } from 'sprintf-js';

@Component({
  selector: 'gpf-genotype-preview-field',
  templateUrl: './genotype-preview-field.component.html',
  styleUrls: ['./genotype-preview-field.component.css']
})
export class GenotypePreviewFieldComponent implements OnChanges, OnInit {
  @Input() value: any;
  @Input() field: string;
  @Input() format: string;
  @Input() genome: string;

  formattedValue: string;
  private UCSCLink: string;

  constructor(
    private datasetsService: DatasetsService,
  ) { }

  ngOnChanges() {
    this.formattedValue = this.formatValue();
    console.log(this.genome)
    if (this.genome) {
      this.UCSCLink = this.getUCSCLink(this.genome);
    }
  }

  ngOnInit() {
    // console.log(this.genome)
    // this.UCSCLink = this.getUCSCLink(this.genome);
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

  getUCSCLink(genome): string {
    let link: string;
    if (genome === 'hg19') {
      link = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr${this.genome}`;
    } else if (genome === 'hg38') {
      link = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=${this.genome}`;
    }
    return link;
  }
}
