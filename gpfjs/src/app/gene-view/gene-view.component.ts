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
  svgHeight;
  x;
  brush;
  doubleClickTimer;

  constructor(
  ) {}

  ngOnInit() {
    this.x = d3.scaleLinear()
    .domain([0, 0])
    .range([0, this.svgWidth]);
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.setDefaultScale();
      this.drawGene();
    }
  }

  drawGene() {
    this.svgHeight = this.gene.transcripts.length * 50;

    d3.select('#svg-container').selectAll('svg').remove();

    this.svgElement = d3.select('#svg-container')
    .append('svg')
    .attr('width', this.svgWidth)
    .attr('height', this.svgHeight);

    let transcriptYPosition = 20;
    for (let i = 0; i < this.gene.transcripts.length; i++) {
      this.drawTranscript(i, transcriptYPosition);
      transcriptYPosition += 50;
    }

    this.brush = d3.brushX().extent([[0, 0], [this.svgWidth, this.svgHeight]])
    .on('end', this.brushEndEvent);

    this.svgElement.append('g')
    .attr('class', 'brush')
    .call(this.brush);
  }

  brushEndEvent = () => {
    const extent = d3.event.selection;

    if (!extent) {
      if (!this.doubleClickTimer) {
        this.doubleClickTimer = setTimeout(this.resetTimer, 250);
        return;
      }
      this.setDefaultScale();
    } else {
      this.x.domain([this.x.invert(extent[0]), this.x.invert(extent[1])]);
      this.svgElement.select('.brush').call(this.brush.move, null);
    }
    this.drawGene();
  }

  resetTimer = () => {
    this.doubleClickTimer = null;
  }

  drawTranscript(transcriptId: number, yPos: number) {
    let lastEnd = null;

    for (const exon of this.gene.transcripts[transcriptId].exons) {
      if (lastEnd) {
        this.drawIntron(lastEnd, exon.start, yPos);
      }
      this.drawExon(exon.start, exon.stop, yPos);

      lastEnd = exon.stop;
    }
  }

  drawExon(xStart: number, xEnd: number, y: number) {
    this.drawRect(xStart, xEnd, y, 10, 'Exon ?/?');
  }

  drawIntron(xStart: number, xEnd: number, y: number) {
    this.drawRect(xStart, xEnd, y + 4, 2, 'Intron ?/?');
  }

  drawRect(xStart: number, xEnd: number, y: number, height: number, svgTitle: string) {
    const width = this.x(xEnd) - this.x(xStart);

    this.svgElement.append('rect')
    .attr('height', height)
    .attr('width', width)
    .attr('x', this.x(xStart))
    .attr('y', y)
    .append('svg:title').text(svgTitle);
  }

  setDefaultScale() {
    let domainBeginning = this.gene.transcripts[0].exons[0].start;
    let domainEnding = this.gene.transcripts[0].exons[this.gene.transcripts[0].exons.length - 1].stop;

    let transcriptStart;
    let transcriptEnd;

    for (let i = 1; i < this.gene.transcripts.length; i++) {
      transcriptStart = this.gene.transcripts[i].exons[0].start;
      if (transcriptStart < domainBeginning) {
        domainBeginning = transcriptStart;
      }

      transcriptEnd = this.gene.transcripts[i].exons[this.gene.transcripts[i].exons.length - 1].stop;
      if (transcriptEnd > domainEnding) {
        domainEnding = transcriptEnd;
      }
    }

    this.x.domain([domainBeginning, domainEnding]);
  }
}
