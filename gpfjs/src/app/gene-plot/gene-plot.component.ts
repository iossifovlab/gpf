import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { Gene, Transcript } from 'app/gene-browser/gene';
import { GenePlotModel, GenePlotScaleState, GenePlotZoomHistory } from 'app/gene-plot/gene-plot';
import { SummaryAllele, SummaryAllelesArray } from 'app/gene-browser/summary-variants';
import * as d3 from 'd3';
import * as draw from 'app/utils/svg-drawing';

@Component({
  selector: 'gpf-gene-plot',
  templateUrl: './gene-plot.component.html',
  styleUrls: ['./gene-plot.component.css'],
  host: {'(document:keydown)': 'handleKeyboardEvent($event)'}
})
export class GenePlotComponent implements OnChanges {
  @Input() public readonly gene: Gene;
  @Input() public readonly variantsArray: SummaryAllelesArray;
  @Input() private readonly frequencyDomain: [number, number];
  @Input() private readonly yAxisLabel: string;
  @Input() public readonly allVariantsCounts: [number, number];

  @Output() public selectedRegion = new EventEmitter<[number, number]>();
  @Output() public selectedFrequencies = new EventEmitter<[number, number]>();

  private readonly constants = {
    svgContainerId: '#svg-container',
    xAxisTicks: 12,
    fontSize: 10,
    minDomainDistance: 12,
    // in percentages
    axisSizes: { domain: 0.90, subdomain: 0.05 },
    // in pixels
    frequencyPlotSize: 300,
    frequencyPlotPadding: 30, // Padding between the frequency plot and the transcripts
    transcriptHeight: 15,
    denovoSpacing: 22,
    margin: { top: 10, right: 30, left: 120, bottom: 15 },
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

  private readonly svgWidth = 2000;
  private subdomainAxisY: number;
  private denovoAxisY: number;
  private svgElement: d3.Selection<SVGSVGElement, unknown, HTMLElement, any>;
  private plotElement: d3.Selection<SVGGElement, unknown, HTMLElement, any>;
  private brush;
  private doubleClickTimer;
  private genePlotModel: GenePlotModel;
  public zoomHistory: GenePlotZoomHistory;
  public showTranscripts = true;
  public condenseIntrons = true;
  private normalRange: number[];
  private condensedRange: number[];
  private denovoLevels: number;
  private denovoAllelesSpacings: Map<string, number>;

  constructor() {
    this.scale.x = d3.scaleLinear();
    this.scale.y = d3.scaleLog();
    this.scale.ySubdomain = d3.scaleLinear();
    this.scale.yDenovo = d3.scalePoint();
    this.subdomainAxisY = this.constants.frequencyPlotSize * this.constants.axisSizes.domain;
    this.denovoAxisY = this.subdomainAxisY + (this.constants.frequencyPlotSize * this.constants.axisSizes.subdomain);
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (!('gene' in changes) || this.gene === undefined) {
      // The initialization code below is only relevant when the gene is changed
      this.redraw();
      return;
    }

    this.genePlotModel = new GenePlotModel(this.gene, this.plotWidth);
    this.normalRange = this.genePlotModel.normalRange;
    this.condensedRange = this.genePlotModel.condensedRange;

    d3.select(this.constants.svgContainerId)
      .selectAll('*')
      .remove();

    this.calculateDenovoAllelesSpacings();

    this.svgElement = d3.select(this.constants.svgContainerId)
      .append('svg')
      .attr('width', '100%')
      .attr('max-height', `${this.svgHeight}`)
      .attr('viewBox', `0 0 ${this.svgWidth} ${this.svgHeight}`)
      .attr('preserveAspectRatio', 'none');

    this.plotElement = this.svgElement.append('g')
      .attr('id', 'plot')
      .attr('transform', `translate(${this.constants.margin.left}, ${this.constants.margin.top})`);

    this.brush = d3.brush()
      .extent([[0, 0], [this.plotWidth, this.frequencyPlotHeight]])
      .on('end', this.focusRegion);

    this.scale.x
      .domain(this.genePlotModel.domain)
      .range(this.condenseIntrons ? this.condensedRange : this.normalRange);
    this.scale.y
      .domain(this.frequencyDomain)
      .range([this.subdomainAxisY, 0]);
    this.scale.ySubdomain
      .domain([0, this.frequencyDomain[0]])
      .range([this.denovoAxisY, this.subdomainAxisY]);
    // The yDenovo scale is set in calculateDenovoAllelesSpacings for convenience

    this.axis.x = d3.axisBottom(this.scale.x).tickValues(this.xAxisTicks);
    this.axis.y = d3.axisLeft(this.scale.y).tickValues(this.yAxisTicks).tickFormat(d3.format('1'));
    this.axis.ySubdomain = d3.axisLeft(this.scale.ySubdomain).tickValues([0]);
    this.axis.yDenovo = d3.axisLeft(this.scale.yDenovo).tickValues([]);

    this.zoomHistory = new GenePlotZoomHistory(
      new GenePlotScaleState(
        this.genePlotModel.domain, this.scale.x.range(), 0, this.frequencyDomain[1], this.condenseIntrons
      )
    );

    this.redraw();
  }

  private get plotWidth(): number {
    return this.svgWidth
      - this.constants.margin.left
      - this.constants.margin.right;
  }

  private get svgHeight(): number {
    // +1 transcript if transcripts are drawn due to the extra padding between the collapsed and normal transcripts
    const transcriptsCount = (this.showTranscripts ? this.genePlotModel.gene.transcripts.length + 1 : 0) + 1;
    return this.frequencyPlotHeight
      + this.constants.margin.top
      + this.constants.margin.bottom
      + this.constants.frequencyPlotPadding
      + (transcriptsCount * this.constants.transcriptHeight);
  }

  private get frequencyPlotHeight(): number {
    return this.constants.frequencyPlotSize + (this.denovoLevels * this.constants.denovoSpacing);
  }

  private get xDomain(): [number, number] {
    const xDomain = this.scale.x.domain();
    return [xDomain[0], xDomain[xDomain.length - 1]];
  }

  private set xDomain(domain: [number, number]) {
    this.normalRange = this.genePlotModel.buildRange(...domain, this.plotWidth, false);
    this.condensedRange = this.genePlotModel.buildRange(...domain, this.plotWidth, true);
    this.scale.x
      .domain(this.genePlotModel.buildDomain(...domain))
      .range(this.condenseIntrons ? this.condensedRange : this.normalRange);
    this.axis.x.tickValues(this.xAxisTicks);
  }

  private get xAxisTicks(): number[] {
    const ticks = [];
    const axisLength = this.plotWidth;
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

  public resetPlot(): void {
    this.scale.x
      .domain(this.genePlotModel.domain)
      .range(this.condenseIntrons ? this.genePlotModel.condensedRange : this.genePlotModel.normalRange);
    this.axis.x.tickValues(this.xAxisTicks);
    this.selectedRegion.emit(this.xDomain);
    this.selectedFrequencies.emit([0, this.frequencyDomain[1]]);
    this.zoomHistory.addStateToHistory(
      new GenePlotScaleState(
        this.scale.x.domain(), this.scale.x.range(), 0, this.frequencyDomain[1], this.condenseIntrons
      )
    );
    this.redraw();
  }

  public redraw(): void {
    this.calculateDenovoAllelesSpacings();
    // Update SVG element with newly-calculated height and clear all child elements
    this.svgElement
      .attr('max-height', `${this.svgHeight}`)
      .attr('viewBox', `0 0 ${this.svgWidth} ${this.svgHeight}`)
      .select('#plot')
      .selectAll('*')
      .remove();

    this.drawPlot();

    this.plotElement.append('g')
      .call(this.brush);

    this.drawVariants();
    this.drawGene();
  }

  public toggleCondenseIntrons() {
    this.condenseIntrons = !this.condenseIntrons;
    const range = this.genePlotModel.buildRange(...this.xDomain, this.plotWidth, this.condenseIntrons);
    this.scale.x.range(range);
    this.axis.x.tickValues(this.xAxisTicks);
    this.zoomHistory.addStateToHistory(
      new GenePlotScaleState(
        this.scale.x.domain(), range,
        this.zoomHistory.currentState.yMin, this.zoomHistory.currentState.yMax,
        this.condenseIntrons
      )
    );
    this.redraw();
  }

  private drawPlot(): void {
    this.plotElement.append('g')
      .attr('id', 'xAxis')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .attr('transform', `translate(0, ${this.frequencyPlotHeight})`)
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
    this.plotElement.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - this.constants.margin.left / 2)
      .attr('x', 0 - (this.constants.frequencyPlotSize / 2))
      .style('text-anchor', 'middle')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .text(this.yAxisLabel);
    this.plotElement.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - this.constants.margin.left / 2)
      .attr('x', 0 - ((this.constants.frequencyPlotSize + this.frequencyPlotHeight) / 2))
      .style('text-anchor', 'middle')
      .style('font', `${this.constants.fontSize}px sans-serif`)
      .text('Denovo');
    // Denovo rectangle
    this.plotElement
      .append('rect')
      .attr('height', this.frequencyPlotHeight - this.scale.ySubdomain(0))
      .attr('width', this.plotWidth)
      .attr('x', 1)
      .attr('y', this.scale.ySubdomain(0))
      .attr('fill', '#FFAD18')
      .attr('fill-opacity', '0.25');
  }

  private drawVariants(): void {
    const variantsElement = this.plotElement.append('g').attr('id', 'variants');
    for (const allele of this.variantsArray.summaryAlleles) {
      const allelePosition = this.scale.x(Math.max(allele.position, this.xDomain[0]));
      const alleleEndPosition = this.scale.x(Math.min(allele.endPosition, this.xDomain[1]));
      const alleleTitle = `Effect type: ${allele.effect}\nVariant position: ${allele.location}`;
      const alleleHeight = this.getAlleleHeight(allele);
      const color = draw.affectedStatusColors[allele.affectedStatus];

      if (allele.seenAsDenovo) {
        if (allele.isCNV()) {
          const cnvLength = alleleEndPosition - allelePosition;
          draw.surroundingRectangle(
            variantsElement, allelePosition + cnvLength / 2,
            alleleHeight, color, alleleTitle, 1, cnvLength
          );
        } else {
          draw.surroundingRectangle(variantsElement, allelePosition, alleleHeight, color, alleleTitle);
        }
      }

      if (allele.isLGDs()) {
        draw.star(variantsElement, allelePosition, alleleHeight, color, alleleTitle);
      } else if (allele.isMissense()) {
        draw.triangle(variantsElement, allelePosition, alleleHeight, color, alleleTitle);
      } else if (allele.isSynonymous()) {
        draw.circle(variantsElement, allelePosition, alleleHeight, color, alleleTitle);
      } else if (allele.isCNVPlus()) {
        draw.rect(
          variantsElement, allelePosition, alleleEndPosition,
          alleleHeight - 3, 6, color, 1, alleleTitle
        );
      } else if (allele.isCNVPMinus()) {
        draw.rect(
          variantsElement, allelePosition, alleleEndPosition,
          alleleHeight - 0.5, 1, color, 1, alleleTitle
        );
      } else {
        draw.dot(variantsElement, allelePosition, alleleHeight, color, alleleTitle);
      }
    }
  }

  private drawGene(): void {
    const collapsedTranscriptElement = this.plotElement.append('g').attr('id', 'collapsedTranscript');
    let transcriptY = this.frequencyPlotHeight + this.constants.frequencyPlotPadding;
    this.drawTranscript(collapsedTranscriptElement, this.genePlotModel.gene.collapsedTranscript, transcriptY);

    if (this.showTranscripts) {
      transcriptY += this.constants.transcriptHeight; // Add some extra padding after the collapsed transcript
      const transcriptsElement = this.plotElement.append('g').attr('id', 'transcripts');
      for (const geneViewTranscript of this.genePlotModel.gene.transcripts) {
        transcriptY += this.constants.transcriptHeight;
        this.drawTranscript(transcriptsElement, geneViewTranscript, transcriptY);
      }
    }
  }

  private drawTranscript(svgGroup, transcript: Transcript, yPos: number) {
    const domainMin = this.scale.x.domain()[0];
    const domainMax = this.scale.x.domain()[this.scale.x.domain().length - 1];
    const transcriptId = transcript.transcriptId;
    const segments = transcript.segments.filter(
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
      this.drawChromosomeLabels(svgGroup, yPos);
    }
    this.drawUTRLabels(
      svgGroup, firstSegmentStart, lastSegmentStop, yPos + brushSize.coding / 2, transcript.strand
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
    const [lUTR, rUTR] = (strand === '+') ? [`5'`, `3'`] : [`3'`, `5'`]; // Choose strand direction
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

  private drawChromosomeLabels(element, yPos: number) {
    const [domainMin, domainMax] = this.xDomain;
    for (const [chromosome, range] of this.gene.chromosomes) {
      if (range[1] < domainMin || range[0] > domainMax) {
        continue;
      }
      const [fromX, toX] = [Math.max(range[0], domainMin), Math.min(range[1], domainMax)];
      draw.hoverText(
        element, (this.scale.x(fromX) + this.scale.x(toX)) / 2 + 50, yPos - 5, `Chromosome: ${chromosome}`, `Chromosome: ${chromosome}`, this.constants.fontSize
      );
    }
  }

  private getAlleleHeight(allele: SummaryAllele): number {
    if (allele.frequency >= this.frequencyDomain[0] && allele.frequency <= this.frequencyDomain[1]) {
      return this.scale.y(allele.frequency);
    } else if (allele.seenAsDenovo && !allele.frequency) {
      return this.scale.yDenovo(this.denovoAllelesSpacings.get(allele.svuid));
    } else {
      return this.scale.ySubdomain(allele.frequency);
    }
  }

  private yToFreq(y: number): number {
    if (y < this.scale.ySubdomain.range()[0]) {
      return this.scale.y.invert(y);
    } else if (y < this.scale.yDenovo.range()[0]) {
      return this.scale.ySubdomain.invert(y);
    } else {
      return 0;
    }
  }

  private focusRegion = () => {
    const extent = d3.event.selection;

    // Double-click
    if (!extent) {
      if (!this.doubleClickTimer) {
        this.doubleClickTimer = setTimeout(() => { this.doubleClickTimer = null; }, 250);
      } else {
        this.resetPlot();
      }
      return;
    }

    if (this.xDomain[1] - this.xDomain[0] > this.constants.minDomainDistance) {
      const [x1, x2] = [extent[0][0], extent[1][0]];
      let [domainMin, domainMax] = [
        Math.round(this.scale.x.invert(Math.min(x1, x2))),
        Math.round(this.scale.x.invert(Math.max(x1, x2)))
      ];
      if (domainMax - domainMin < this.constants.minDomainDistance) {
        const center = domainMin + Math.round((domainMax - domainMin) / 2);
        domainMin = center - (this.constants.minDomainDistance / 2);
        domainMax = center + (this.constants.minDomainDistance / 2);
      }
      this.xDomain = [domainMin, domainMax];
      this.selectedRegion.emit([domainMin, domainMax]);
    }

    const freqSelection: [number, number] = [this.yToFreq(extent[0][1]), this.yToFreq(extent[1][1])];
    this.selectedFrequencies.emit([Math.min(...freqSelection), Math.max(...freqSelection)]);

    this.zoomHistory.addStateToHistory(
      new GenePlotScaleState(
        this.scale.x.domain(), this.scale.x.range(),
        Math.min(...freqSelection), Math.max(...freqSelection), this.condenseIntrons
      )
    );
  }

  private calculateDenovoAllelesSpacings(): void {
    const denovoAlleles = this.variantsArray.summaryAlleles
      .filter(sa => sa.seenAsDenovo && !sa.frequency)
      .sort((sa, sa2) => sa.position - sa2.position);

    const leveledDenovos: SummaryAllele[][] = [[]];
    this.denovoAllelesSpacings = new Map<string, number>();
    for (const allele of denovoAlleles) {
      // try putting in one of current levels
      for (let level = 0; level < leveledDenovos.length; level++) {
        if (leveledDenovos[level].every(sa => !sa.intersects(allele))) {
          leveledDenovos[level].push(allele);
          this.denovoAllelesSpacings.set(allele.svuid, level);
          break;
        }
      }
      // if no space, add another
      if (!this.denovoAllelesSpacings.has(allele.svuid)) {
        leveledDenovos.push([allele]);
        this.denovoAllelesSpacings.set(allele.svuid, leveledDenovos.length - 1);
      }
    }
    this.denovoLevels = leveledDenovos.length;
    this.scale.yDenovo
      .domain(Object.keys(leveledDenovos))
      .range([this.denovoAxisY, this.frequencyPlotHeight]);
  }

  public undo(): void {
    this.zoomHistory.moveToPrevious();
    this.restoreState(this.zoomHistory.currentState);
  }

  public redo(): void {
    this.zoomHistory.moveToNext();
    this.restoreState(this.zoomHistory.currentState);
  }

  public reset(): void {
    this.resetPlot();
    this.zoomHistory.reset();
  }

  private restoreState(state: GenePlotScaleState): void {
    this.scale.x
      .domain(state.xDomain)
      .range(state.xRange);
    this.axis.x.tickValues(this.xAxisTicks);
    this.condenseIntrons = state.condenseToggled;
    this.selectedFrequencies.emit([state.yMin, state.yMax]);
    this.selectedRegion.emit(this.xDomain);
    this.redraw();
  }

  private handleKeyboardEvent($event): void {
    if ($event.target.id === 'search-box') {
      return;
    }

    const keyPressed: string = $event.key;
    const isCtrlPressed = $event.ctrlKey;

    if (keyPressed === 'z' || (isCtrlPressed && keyPressed === 'z')) {
      this.undo();
    } else if (keyPressed === 'y' || (isCtrlPressed && keyPressed === 'y')) {
      this.redo();
    } else if (keyPressed === '5') {
      this.reset();
    }
  }
}
