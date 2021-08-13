import { Component, EventEmitter, Input, Output, OnChanges } from '@angular/core';
import { Gene, GeneViewTranscript, GeneViewSummaryAllelesArray } from 'app/gene-view/gene';
import { GeneViewModel } from 'app/gene-view/gene-view';
import * as d3 from 'd3';
import * as draw from 'app/utils/svg-drawing';

@Component({
  selector: 'gpf-gene-plot',
  templateUrl: './gene-plot.component.html',
  styleUrls: ['./gene-plot.component.css']
})
export class GenePlotComponent implements OnChanges {
  @Input() private readonly gene: Gene;
  @Input() private readonly variantsArray: GeneViewSummaryAllelesArray;
  @Input() private readonly frequencyDomain: [number, number];
  @Input() private readonly yAxisLabel: string;

  @Output() public selectedRegion = new EventEmitter<[number, number]>();
  @Output() public selectedFrequencies = new EventEmitter<[number, number]>();

  private readonly constants = {
    svgContainerId: '#svg-container',
    xAxisTicks: 12,
    fontSize: 8,
    // in percentages
    axisSizes: { domain: 0.90, subdomain: 0.05 },
    // in pixels
    frequencyPlotSize: 300,
    frequencyPlotPadding: 30, // Padding between the frequency plot and the transcripts
    transcriptHeight: 12,
    margin: { top: 10, right: 30, left: 120, bottom: 0 },
    exonThickness: { normal: 3, collapsed: 6 },
    cdsThickness: { normal: 6, collapsed: 12 },
  };

  private readonly scale = {
    x: null,
    y: null,
    ySubdomain: null,
    yDenovo: null,
  };

  private readonly axis = {
    x: null,
    y: null,
    ySubdomain: null,
    yDenovo: null,
  };

  private readonly svgWidth = 1000;
  private svgElement: d3.Selection<SVGSVGElement, unknown, HTMLElement, any>;
  private plotElement: d3.Selection<SVGGElement, unknown, HTMLElement, any>;
  private geneViewModel: GeneViewModel;
  private condenseIntrons = true;
  private drawTranscripts = true;

  constructor() {
    this.scale.x = d3.scaleLinear();
    this.scale.y = d3.scaleLog();
    this.scale.ySubdomain = d3.scaleLinear();
    this.scale.yDenovo = d3.scalePoint();
  }

  public ngOnChanges(): void {
    if (this.gene === undefined) {
      return;
    }

    console.log("Running onChanges...");

    this.geneViewModel = new GeneViewModel(this.gene, this.plotWidth);

    this.svgElement = d3.select(this.constants.svgContainerId)
      .append('svg')
      .attr('width', '60%')
      .attr('max-height', `${this.svgHeight}`)
      .attr('viewBox', `0 0 ${this.svgWidth} ${this.svgHeight}`);
      // .attr('preserveAspectRatio', 'xMinYMin meet');

    this.plotElement = this.svgElement.append('g')
      .attr('id', 'plot')
      .attr('transform', `translate(${this.constants.margin.left}, ${this.constants.margin.top})`);

    const subdomainAxisY = this.constants.frequencyPlotSize * this.constants.axisSizes.domain;
    const zeroAxisY = subdomainAxisY + (this.constants.frequencyPlotSize * this.constants.axisSizes.subdomain);

    this.scale.x
      .domain(this.geneViewModel.domain)
      .range(this.condenseIntrons ? this.geneViewModel.condensedRange : this.geneViewModel.normalRange);
    this.scale.y
      .domain(this.frequencyDomain)
      .range([subdomainAxisY, 0]);
    this.scale.ySubdomain
      .domain([0, this.frequencyDomain[0]])
      .range([zeroAxisY, subdomainAxisY]);
    this.scale.yDenovo
      .domain(['Denovo'])
      .range([this.constants.frequencyPlotSize, zeroAxisY]);

    this.axis.x = d3.axisBottom(this.scale.x).tickValues(this.xAxisTicks);
    this.axis.y = d3.axisLeft(this.scale.y).tickValues(this.yAxisTicks).tickFormat(d3.format('1'));
    this.axis.ySubdomain = d3.axisLeft(this.scale.ySubdomain).tickValues([0]);
    this.axis.yDenovo = d3.axisLeft(this.scale.yDenovo);

    this.redraw();
  }

  private get plotWidth(): number {
    return this.svgWidth
      - this.constants.margin.left
      - this.constants.margin.right;
  }

  private get svgHeight(): number {
    // +1 transcript if transcripts are drawn due to the extra padding between the collapsed and normal transcripts
    const transcriptsCount = (this.drawTranscripts ? this.geneViewModel.geneViewTranscripts.length + 1 : 0) + 1;
    return this.constants.frequencyPlotSize
      + this.constants.margin.top
      + this.constants.margin.bottom
      + this.constants.frequencyPlotPadding
      + (transcriptsCount * this.constants.transcriptHeight);
  }

  private get xAxisTicks(): number[] {
    const ticks = [];
    const axisLength = this.plotWidth;
    // const axisLength = this.scale.x.range()[this.scale.x.range().length - 1] - this.scale.x.range()[0];
    const increment = Math.round(axisLength / (this.constants.xAxisTicks - 1));
    for (let i = 0; i < axisLength; i += increment) {
      ticks.push(Math.round(this.scale.x.invert(i)));
    }
    return ticks;
  }

  private get yAxisTicks(): number[] {
    const ticks = [];
    for (let i = this.frequencyDomain[0]; i <= this.frequencyDomain[1]; i *= 10) {
      ticks.push(i);
    }
    return ticks;
  }

  private resetPlot(): void {
    this.scale.x
      .domain(this.geneViewModel.domain)
      .range(this.condenseIntrons ? this.geneViewModel.condensedRange : this.geneViewModel.normalRange);
    this.selectedRegion.emit(this.scale.x.domain);
    this.selectedFrequencies.emit(this.frequencyDomain);
  }

  private redraw(): void {
    console.log('Redrawing!');
    // Update SVG element with newly-calculated height and clear all child elements
    this.svgElement
      .transition()
      .duration(125)
      .attr('max-height', `${this.svgHeight}`)
      .attr('viewBox', `0 0 ${this.svgWidth} ${this.svgHeight}`)
      .select('#plot')
      .selectAll('*')
      .remove();
    this.drawPlot();
    // this.drawVariants();
    this.drawGene();
  }

  private drawPlot(): void {
    this.plotElement.append('g')
      .attr('id', 'xAxis')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .attr('transform', `translate(0, ${this.constants.frequencyPlotSize})`)
      .call(this.axis.x);
    this.plotElement.append('g')
      .attr('id', 'yAxis')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .call(this.axis.y);
    this.plotElement.append('g')
      .attr('id', 'ySubdomainAxis')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .call(this.axis.ySubdomain);
    this.plotElement.append('g')
      .attr('id', 'yDenovoAxis')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .call(this.axis.yDenovo);
  }

  private drawVariants(): void {}

  private drawGene(): void {
    const summedTranscriptElement = this.plotElement.append('g').attr('id', 'summedTranscript');
    let transcriptY = this.constants.frequencyPlotSize + this.constants.frequencyPlotPadding;
    this.drawTranscript(summedTranscriptElement, this.geneViewModel.collapsedGeneViewTranscript, transcriptY);

    if (this.drawTranscripts) {
      transcriptY += this.constants.transcriptHeight; // Add some extra padding after the collapsed transcript
      const transcriptsElement = this.plotElement.append('g').attr('id', 'transcripts');
      for (const geneViewTranscript of this.geneViewModel.geneViewTranscripts) {
        transcriptY += this.constants.transcriptHeight;
        this.drawTranscript(transcriptsElement, geneViewTranscript, transcriptY);
      }
    }
  }

  private drawTranscript(svgGroup, geneViewTranscript: GeneViewTranscript, yPos: number) {
    const domainMin = this.scale.x.domain()[0];
    const domainMax = this.scale.x.domain()[this.scale.x.domain().length - 1];
    const transcriptId = geneViewTranscript.transcript.transcript_id;
    const segments = geneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0
    );

    if (segments.length === 0) {
      return;
    }

    const firstSegmentStart = Math.max(segments[0].start, domainMin);
    const lastSegmentStop = Math.min(segments[segments.length - 1].stop, domainMax);

    let brushSize = {
      nonCoding: this.constants.exonThickness.normal,
      coding: this.constants.cdsThickness.normal
    };

    if (transcriptId === 'collapsed') {
      brushSize = {
        nonCoding: this.constants.exonThickness.collapsed,
        coding: this.constants.cdsThickness.collapsed
      };
      this.drawChromosomeLabels(svgGroup, yPos, geneViewTranscript);
    }
    this.drawUTRLabels(
      svgGroup, firstSegmentStart, lastSegmentStop, yPos + brushSize.coding / 2, geneViewTranscript.strand
    );

    let exonsLength = 0;
    for (const segment of segments) {
      const xStart = this.scale.x(Math.max(domainMin, segment.start));
      const xStop = this.scale.x(Math.min(domainMax, segment.stop));

      if (segment.isExon) {
        this.drawExon(svgGroup, xStart, xStop, yPos, segment.label, segment.isCDS, brushSize);
        exonsLength += segment.stop - segment.start;
      } else if (!segment.isSpacer) {
        this.drawIntron(svgGroup, xStart, xStop, yPos, segment.label, brushSize);
      }
    }

    if (transcriptId !== 'collapsed') {
      const formattedExonsLength = this.formatExonsLength(exonsLength);
      draw.hoverText(
        svgGroup,
        this.scale.x(firstSegmentStart) - 20,
        yPos + brushSize.coding / 2,
        formattedExonsLength,
        `Transcript id: ${transcriptId}\nExons length: ${this.commaSeparateNumber(exonsLength)}`,
        this.constants.fontSize
      );
    }
  }

  private drawExon(svgGroup, xStart: number, xEnd: number, y: number, title: string, cds: boolean, brushSize) {
    let rectThickness = brushSize.nonCoding;
    if (cds) {
      rectThickness = brushSize.coding;
      title += ' [CDS]';
    } else {
      y += (brushSize.coding - brushSize.nonCoding) / 2;
    }
    draw.rect(svgGroup, xStart, xEnd, y, rectThickness, 'black', 1, title);
  }

  private drawIntron(svgGroup, xStart: number, xEnd: number, y: number, title: string, brushSize) {
    draw.line(svgGroup, xStart, xEnd, y + brushSize.coding / 2, title);
  }

  private drawUTRLabels(svgGroup, xStart: number, xEnd: number, y: number, strand: string) {
    const [lUTR, rUTR] = (strand === '+') ? [`5'`, `3'`] : [`3'`, `5'`];
    draw.hoverText(svgGroup, this.scale.x(xStart) - 5, y, lUTR, `UTR ${lUTR}`, this.constants.fontSize);
    draw.hoverText(svgGroup, this.scale.x(xEnd) + 10, y, rUTR, `UTR ${rUTR}`, this.constants.fontSize);
  }

  private commaSeparateNumber(number: number): string {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' bp';
  }

  private formatExonsLength(exonsLength: number): string {
    if (exonsLength < 1000) {
      return `~${exonsLength} bp`;
    } else if (exonsLength < 1000000) {
      return `~${Math.round(exonsLength / 100) / 10} kbp`;
    } else {
      return `~${Math.round(exonsLength / 100000) / 10} mbp`;
    }
  }

  private drawChromosomeLabels(element, yPos: number, geneViewTranscript: GeneViewTranscript) {
    const domainMin = this.scale.x.domain()[0];
    const domainMax = this.scale.x.domain()[this.scale.x.domain().length - 1];
    const selectedChromosomes = {};
    for (const [chromosome, range] of Object.entries(geneViewTranscript.chromosomes)) {
      if (range[1] < domainMin || range[0] > domainMax) {
        continue;
      } else {
        selectedChromosomes[chromosome] = range;
      }
    }

    let from, to: number;
    for (const [chromosome, range] of Object.entries(selectedChromosomes)) {
      from = Math.max(range[0], domainMin);
      to = Math.min(range[1], domainMax);
      draw.hoverText(
        element, (this.scale.x(from) + this.scale.x(to)) / 2 + 50, yPos - 5, `Chromosome: ${chromosome}`, `Chromosome: ${chromosome}`, this.constants.fontSize
      );
    }
  }
}
