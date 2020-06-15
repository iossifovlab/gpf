import { Component, OnInit, Input, OnChanges } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from './gene';

@Component({
  selector: 'gpf-gene-view',
  templateUrl: './gene-view.component.html',
  styleUrls: ['./gene-view.component.css']
})
export class GeneViewComponent implements OnInit, OnChanges {
  @Input() gene: Gene;

  svgElement;
  svgWidth = 1000;
  svgHeight = 150;

  constructor(
  ) {}

  ngOnInit() {
    this.svgElement = d3.select('#svg-container')
    .append('svg')
    .attr('width', this.svgWidth)
    .attr('height', this.svgHeight);
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.svgElement.selectAll('*').remove();
      this.drawGene();
    }
  }

  drawGene() {
    this.drawTranscript(0);
    this.drawTranscript(1);

    const brush = d3.brushX().extent([[0, 0], [this.svgWidth, this.svgHeight]])
    .on('start', this.brushStartEvent)
    .on('brush', this.brushBrushEvent)
    .on('end', this.brushEndEvent);

    this.svgElement.append('g')
    .call(brush);
  }

  brushStartEvent() {
    console.log('brush start event');
  }

  brushBrushEvent() {
    console.log('brush brush event');
  }

  brushEndEvent() {
    const extent = d3.event.selection;
    console.log('brush end event');
    console.log(extent);
  }

  drawTranscript(transcriptId: number) {
    let x = 0;
    let y = 0;
    let exonAndIntronLengths: number[];
    let isExon = true;

    if (transcriptId === 0) {
      y = 20;
    } else {
      y = 120;
    }

    exonAndIntronLengths = this.getExonAndIntronLengths(this.gene.transcripts[transcriptId].exons);
    exonAndIntronLengths = this.scaleDownLengths(exonAndIntronLengths);

    for (const d of exonAndIntronLengths) {
      if (isExon) {
        this.svgElement.append('rect')
        .attr('height', 10)
        .attr('width', d)
        .attr('x', x)
        .attr('y', y)
        .append('svg:title').text('Exon ?/?');
      } else {
        this.svgElement.append('rect')
        .attr('height', 2)
        .attr('width', d)
        .attr('x', x)
        .attr('y', y + 4)
        .append('svg:title').text('Intron ?/?');
      }

      x += d;
      isExon = !isExon;
    }
  }

  getExonAndIntronLengths(exonsObj: object) {
    const exonAndIntronLengths: number[] = [];
    const exons = Object.values(exonsObj);
    let previousExonStop = 0;

    for (const exon of exons) {
      exonAndIntronLengths.push(exon.start - previousExonStop);
      exonAndIntronLengths.push(exon.stop - exon.start);
      previousExonStop = exon.stop;
    }
    exonAndIntronLengths.shift();

    return exonAndIntronLengths;
  }

  scaleDownLengths(lengths: number[]) {
    const scaledLengths: number[] = [];
    const scaleIndex = this.calculateScaleIndex();

    for (const len of lengths) {
      scaledLengths.push(len / scaleIndex);
    }

    return scaledLengths;
  }

  calculateScaleIndex(): number {
    let scaleIndex: number;
    const firstTranscriptLength = this.calculateTotalLength(this.gene.transcripts[0].exons);
    const secondTranscriptLength = this.calculateTotalLength(this.gene.transcripts[1].exons);

    if (firstTranscriptLength > secondTranscriptLength) {
      scaleIndex = firstTranscriptLength / this.svgWidth;
    } else {
      scaleIndex = secondTranscriptLength / this.svgWidth;
    }

    return scaleIndex;
  }

  calculateTotalLength(exonsObj: object) {
    let totalLength: number;

    totalLength = exonsObj[Object.keys(exonsObj).length - 1].stop - exonsObj[0].start;

    return totalLength;
  }
}
