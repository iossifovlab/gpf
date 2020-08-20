import { Component, OnInit, Input, OnChanges } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { QueryService } from 'app/query/query.service';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
// import { Gene } from './gene';

@Component({
  selector: 'gpf-variant-frequency-view',
  templateUrl: './variant-frequency-view.component.html',
  styleUrls: ['./variant-frequency-view.component.css']
})
export class VariantFrequencyViewComponent implements OnInit, OnChanges {
  @Input() gene: Gene;
  @Input() variantsArray: GenotypePreviewVariantsArray;

  svgElement;
  svgWidth = 1000;
  svgHeight = 150;
  x;
  x_axis;

  constructor(
    private queryService: QueryService,
  ) { }

  ngOnInit() {
    this.svgElement = d3.select('#svg-container-asdf')
    .append('svg')
    .attr('width', this.svgWidth)
    .attr('height', this.svgHeight);

    this.x = d3.scaleLinear()
    .domain([0, 0])
    .range([0, this.svgWidth - 20]);
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.setDefaultScale();
      this.x_axis = d3.axisBottom(this.x);
      this.svgElement.append('g').call(this.x_axis);
    }
  }

  setDefaultScale(): void {
    const a = this.gene.transcripts[0].exons;
    const b = this.gene.transcripts[1].exons;

    const domainBeginning = Math.min(a[0].start, b[0].start);
    const domainEnding = Math.max(a[a.length - 1].stop, b[b.length - 1].stop);

    this.x.domain([domainBeginning, domainEnding]);
  }
}
