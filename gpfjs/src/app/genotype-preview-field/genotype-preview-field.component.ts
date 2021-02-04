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

  private formattedValue: string;
  private UCSCLink: string;

  constructor(
    private datasetsService: DatasetsService,
  ) { }

  ngOnChanges() {
    this.formattedValue = this.formatValue();
  }

  ngOnInit() {
    this.datasetsService.getDatasetDetails(this.datasetsService.getSelectedDatasetId())
      .subscribe(res => {
        if (res.genome === 'hg19') {
          this.UCSCLink = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr${this.value}`;
        } else if (res.genome === 'hg38') {
          this.UCSCLink = `http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=${this.value}`;
        }
      }
    );
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
}
