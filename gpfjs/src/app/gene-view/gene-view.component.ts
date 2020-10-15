import { Component, OnInit, Input, OnChanges, Output, EventEmitter } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray, GenotypePreview } from 'app/genotype-preview-model/genotype-preview';
import { Subject } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Transcript, Exon } from 'app/gene-view/gene';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';


class GeneViewSummaryVariant {
  location: string;
  position: number;
  chrom: string;
  variant: string;
  effect: string;
  frequency: number;
  numberOfFamilyVariants: number;
  seenAsDenovo: boolean;

  seenInAffected: boolean;
  seenInUnaffected: boolean;
  svuid: string;

  lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  isLGDs(): boolean {
    if (this.lgds.indexOf(this.effect) !== -1 || this.effect === 'lgds') {
      return true;
    }
    return false;
  }

  isMissense(): boolean {
    if (this.effect === 'missense') {
      return true;
    }
    return false;
  }

  isSynonymous(): boolean {
    if (this.effect === 'synonymous') {
      return true;
    }
    return false;
  }

  static fromPreviewVariant(config, genotypePreview: GenotypePreview): GeneViewSummaryVariant {
    const result = new GeneViewSummaryVariant();

    const location = genotypePreview.get(config.locationColumn);
    result.location = location;
    result.position = Number(location.slice(location.indexOf(':') + 1));
    result.chrom = location.slice(0, location.indexOf(':'));

    let frequency: string = genotypePreview.data.get(config.frequencyColumn);
    if (frequency === '-') {
      frequency = '0.0';
    }
    result.frequency = Number(frequency);

    result.effect = genotypePreview.get(config.effectColumn).toLowerCase();
    result.variant = genotypePreview.get('variant.variant');

    result.numberOfFamilyVariants = 1;

    result.seenAsDenovo = false;
    if (genotypePreview.get('variant.is denovo')) {
      result.seenAsDenovo = true;
    }
    result.seenInAffected = false;
    result.seenInUnaffected = false;
    for (const pedigreeData of genotypePreview.get("genotype")) {
      if (pedigreeData.label > 0) {
        if (pedigreeData.color == "#ffffff") {
          result.seenInUnaffected = true
        } else {
          result.seenInAffected = true
        }
      }
    }

    result.svuid = result.location + ':' + result.variant;

    return result;
  }
}

class GeneViewSummaryVariantsArray {
  summaryVariants: GeneViewSummaryVariant[] = [];

  constructor(summaryVariants: IterableIterator<GeneViewSummaryVariant>) {
    for (const summaryVariant of summaryVariants) {
      this.summaryVariants.push(summaryVariant);
    }
  }

  static fromPreviewVariantsArray(config, previewVariants: GenotypePreviewVariantsArray): GeneViewSummaryVariantsArray {
    const summaryVariants: Map<string, GeneViewSummaryVariant> = new Map();

    for (const genotypePreview of previewVariants.genotypePreviews) {
      const summaryVariant = GeneViewSummaryVariant.fromPreviewVariant(config, genotypePreview);
      const svuid = summaryVariant.svuid;

      if (!summaryVariants.has(svuid)) {
        summaryVariants.set(svuid, summaryVariant);
      } else {
        const mergeSummaryVariant = summaryVariants.get(svuid);
        mergeSummaryVariant.numberOfFamilyVariants += 1;
        if (summaryVariant.seenAsDenovo) {
          mergeSummaryVariant.seenAsDenovo = true;
        }
        if (summaryVariant.seenInAffected) {
          mergeSummaryVariant.seenInAffected = true;
        }
        if (summaryVariant.seenInUnaffected) {
          mergeSummaryVariant.seenInUnaffected = true;
        }
      }
    }
    return new GeneViewSummaryVariantsArray(summaryVariants.values());
  }
}

class GeneViewTranscriptSegment {

  dnaStart: number;
  dnaEnd: number;
  plotStart: number;
  plotEnd: number;
  isExon: boolean;
  isCDS: boolean;

  constructor(
    dnaStart: number,
    dnaEnd: number,
    plotStart: number,
    plotEnd: number,
    isExon: boolean,
    isCDS: boolean
  ) {
    this.dnaStart = dnaStart;
    this.dnaEnd = dnaEnd;
    this.plotStart = plotStart;
    this.plotEnd = plotEnd;
    this.isExon = isExon;
    this.isCDS = isCDS;
  }
}

class GeneViewTranscript {

  transcript: Transcript;
  transcriptSegments: GeneViewTranscriptSegment[] = [];
  collapseIntrons = false;
  collapsedIntronLength = 2000; // in base pairs, not px
  _start: number;
  _stop: number;

  constructor(transcript: Transcript) {
    this.transcript = transcript;
    this.resetStartStop();

    for (let i = 0; i < this.transcript.exons.length; i++) {
      const cdsTransition = GeneViewTranscript.getCDSTransitionPos(
        this.transcript,
        this.transcript.exons[i]
      );

      if (cdsTransition) {
        this.transcriptSegments.push(
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].start, cdsTransition,
            null, null, true, GeneViewTranscript.isInCDS(
              this.transcript, this.transcript.exons[i].start, this.transcript.exons[i].stop
            )
          ),
          new GeneViewTranscriptSegment(
            cdsTransition, this.transcript.exons[i].stop,
            null, null, true, GeneViewTranscript.isInCDS(
              this.transcript, this.transcript.exons[i].start, this.transcript.exons[i].stop
            )
          )
        );
      } else {
        this.transcriptSegments.push(
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].start, this.transcript.exons[i].stop,
            null, null, true, GeneViewTranscript.isInCDS(
              this.transcript, this.transcript.exons[i].start, this.transcript.exons[i].stop
            )
          )
        );
      }

      if (i + 1 < this.transcript.exons.length) {
        this.transcriptSegments.push(new GeneViewTranscriptSegment(
          this.transcript.exons[i].stop, this.transcript.exons[i + 1].start,
          null, null, false, GeneViewTranscript.isInCDS(
            this.transcript, this.transcript.exons[i].stop, this.transcript.exons[i + 1].start
          )
        ));
      }
    }
  }

  static isInCDS(transcript: Transcript, start: number, stop: number) {
    return (start >= transcript.cds[0]) && (stop <= transcript.cds[1]);
  }

  static getCDSTransitionPos(transcript: Transcript, exon: Exon) {
    function inCDS(pos: number) {
      return pos >= transcript.cds[0] && pos <= transcript.cds[1];
    }
    if (inCDS(exon.start) !== inCDS(exon.stop)) {
      if (inCDS(exon.start)) {
        return transcript.cds[1];
      } else {
        return transcript.cds[0];
      }
    } else { return null; }
  }

  static domainFromSegments(segments: GeneViewTranscriptSegment[]): number[] {
    const domain: number[] = [];
    for (let i = 0; i < segments.length; i++) {
      domain.push(segments[i].dnaStart, segments[i].dnaEnd);
    }
    return domain;
  }

  resetStartStop() {
    this.start = this.transcript.exons[0].start;
    this.stop = this.transcript.exons[this.transcript.exons.length - 1].stop;
  }

  get start() {
    return this._start;
  }

  set start(input: number) {
    input = Math.max(input, this.transcript.exons[0].start);
    this._start = input;
  }

  get stop() {
    return this._stop;
  }

  set stop(input: number) {
    input = Math.min(input, this.transcript.exons[this.transcript.exons.length - 1].stop);
    this._stop = input;
  }

  calculateSelectedSegments(): GeneViewTranscriptSegment[] {
    const newSegments = [];
    for (let i = 0; i < this.transcriptSegments.length; i++) {
      const segment: GeneViewTranscriptSegment = this.transcriptSegments[i];
      if (segment.dnaEnd <= this.start || segment.dnaStart >= this.stop) {
        continue;
      }
      const start = Math.max(this.start, this.transcriptSegments[i].dnaStart);
      const stop = Math.min(this.stop, this.transcriptSegments[i].dnaEnd);

      newSegments.push(new GeneViewTranscriptSegment(
        start, stop, null, null, segment.isExon, segment.isCDS
      ));
    }
    return newSegments;
  }

  calculatePlotRanges(plotWidth: number): number[] {
    const selectedSegments = this.calculateSelectedSegments();
    const selectedExonSegments = selectedSegments.filter(segment => segment.isExon);
    const selectedIntronSegments = selectedSegments.filter(segment => !segment.isExon);

    const linearScale = d3.scaleLinear()
    .domain([selectedSegments[0].dnaStart, selectedSegments[selectedSegments.length - 1].dnaEnd])
    .range([0, plotWidth]);

    const intronLengths: number[] = [];

    for (let i = 0; i < selectedIntronSegments.length; i++) {
      let intronLength = selectedIntronSegments[i].dnaEnd - selectedIntronSegments[i].dnaStart;
      if (this.collapseIntrons) {
        intronLength = Math.min(intronLength, this.collapsedIntronLength);
      }
      intronLengths.push(intronLength);
    }

    const newIntronSpace = intronLengths.reduce((a, b) => a + b, 0);
    const exonSpace = selectedExonSegments.reduce((a, b) => a + b.dnaEnd - b.dnaStart, 0);
    const newExonSpace = selectedSegments[selectedSegments.length - 1].dnaEnd - selectedSegments[0].dnaStart - newIntronSpace;
    const newExonRatio = newExonSpace / exonSpace;

    const plotSegments: number[] = [];
    let rollingPosTracker = 0;
    for (let i = 0; i < selectedSegments.length; i++) {
      const segment = selectedSegments[i];
      let segmentLength = segment.dnaEnd - segment.dnaStart;
      if (segment.isExon) {
        segmentLength *= newExonRatio;
      } else if (this.collapseIntrons) {
        segmentLength = Math.min(segmentLength, this.collapsedIntronLength);
      }
      plotSegments.push(
        rollingPosTracker, rollingPosTracker + linearScale(linearScale.domain()[0] + segmentLength),
      );
      rollingPosTracker += linearScale(linearScale.domain()[0] + segmentLength);
    }
    return plotSegments;
  }
}

@Component({
  selector: 'gpf-gene-view',
  templateUrl: './gene-view.component.html',
  styleUrls: ['./gene-view.component.css']
})
export class GeneViewComponent implements OnInit {
  @Input() gene: Gene;
  @Input() variantsArray: GenotypePreviewVariantsArray;
  @Input() streamingFinished$: Subject<boolean>;
  @Output() updateShownTablePreviewVariantsArrayEvent = new EventEmitter<GenotypePreviewVariantsArray>();

  geneBrowserConfig;
  frequencyDomainMin: number;
  frequencyDomainMax: number;
  summaryVariantsArray: GeneViewSummaryVariantsArray;

  margin = { top: 10, right: 70, left: 70, bottom: 0 };
  y_axes_proportions = { domain: 0.70, subdomain: 0.20 };
  svgElement;
  svgWidth = 1200 - this.margin.left - this.margin.right;
  svgHeight;
  svgHeightFreqRaw = 400;
  svgHeightFreq = this.svgHeightFreqRaw - this.margin.top - this.margin.bottom;

  subdomainAxisY = Math.round(this.svgHeightFreq * 0.90);
  zeroAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * 0.05);

  lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  x;
  y;
  y_subdomain;
  y_zero;
  x_axis;
  y_axis;
  y_axis_subdomain;
  y_axis_zero;
  variantsDataRepr = [];
  selectedEffectTypes = ['lgds', 'missense', 'synonymous', 'other'];
  selectedFrequencies;
  showDenovo = true;
  showTransmitted = true;

  geneViewTranscript: GeneViewTranscript;

  brush;
  doubleClickTimer;
  geneTableStats = {
    geneSymbol: '',
    chromosome: '',
    totalFamilyVariants: 0,
    selectedFamilyVariants: 0,
    totalSummaryVariants: 0,
    selectedSummaryVariants: 0,
  };

  constructor(
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
  ) { }

  ngOnInit() {
    this.datasetsService.getSelectedDataset().subscribe(dataset => {
      this.geneBrowserConfig = dataset.geneBrowser;
      this.frequencyDomainMin = this.geneBrowserConfig.domainMin;
      this.frequencyDomainMax = this.geneBrowserConfig.domainMax;
      this.selectedFrequencies = [0, this.frequencyDomainMax];

      this.drawEffectTypesIcons();
      this.drawTransmittedIcons();
      this.drawDenovoIcons();

      this.svgElement = d3.select('#svg-container')
        .append('svg')
        .attr('width', this.svgWidth + this.margin.left + this.margin.right)
        .attr('height', this.svgHeightFreqRaw)
        .append('g')
        .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);

      this.x = d3.scaleLinear()
        .domain([0, 0])
        .range([0, this.svgWidth]);

      this.y = d3.scaleLog()
        .domain([this.frequencyDomainMin, this.frequencyDomainMax])
        .range([this.subdomainAxisY, 0]);

      this.y_subdomain = d3.scaleLinear()
        .domain([0, this.frequencyDomainMin])
        .range([this.zeroAxisY, this.subdomainAxisY]);

      this.y_zero = d3.scalePoint()
        .domain(['0'])
        .range([this.svgHeightFreq, this.zeroAxisY]);
    });
    this.streamingFinished$.subscribe(() => {
      this.summaryVariantsArray = GeneViewSummaryVariantsArray.fromPreviewVariantsArray(
        this.geneBrowserConfig,
        this.variantsArray
      );

      this.updateFamilyVariantsTable();
      this.drawPlot();

      this.geneTableStats.geneSymbol = this.gene.gene;
      this.geneTableStats.chromosome = this.gene.transcripts[0].chrom;
      this.geneTableStats.totalSummaryVariants = this.summaryVariantsArray.summaryVariants.length;
      this.geneTableStats.totalFamilyVariants = this.summaryVariantsArray.summaryVariants.reduce(
        (a, b) => a + b.numberOfFamilyVariants, 0
      );

      this.loadingService.setLoadingStop();
    });
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.geneViewTranscript = new GeneViewTranscript(this.gene.transcripts[0]);
      this.resetGeneTableValues();
      this.setDefaultScale();
      this.drawGene();
    }
  }

  drawTransmittedIcons() {
    this.svgElement = d3.select('#transmitted')
    .attr('width', 80)
    .attr('height', 20);
    this.drawStar(10, 7.5, '#000000');
    this.drawTriangle(30, 8, '#000000');
    this.drawCircle(50, 8, '#000000');
    this.drawDot(70, 8, '#000000');
  }

  drawDenovoIcons() {
    this.svgElement = d3.select('#denovo')
    .attr('width', 80)
    .attr('height', 20);
    this.drawStar(10, 7.5, '#000000');
    this.drawSuroundingSquare(10, 7.5, '#000000');
    this.drawTriangle(30, 8, '#000000');
    this.drawSuroundingSquare(30, 8, '#000000');
    this.drawCircle(50, 8, '#000000');
    this.drawSuroundingSquare(50, 8, '#000000');
    this.drawDot(70, 8, '#000000');
    this.drawSuroundingSquare(70, 8, '#000000');
  }

  drawEffectTypesIcons() {
    this.svgElement = d3.select('#LGDs')
    .attr('width', 20)
    .attr('height', 20);
    this.drawStar(10, 7.5, '#000000');

    this.svgElement = d3.select('#Missense')
    .attr('width', 20)
    .attr('height', 20);
    this.drawTriangle(10, 8, '#000000');

    this.svgElement = d3.select('#Synonymous')
    .attr('width', 20)
    .attr('height', 20);
    this.drawCircle(10, 8, '#000000');

    this.svgElement = d3.select('#Other')
    .attr('width', 20)
    .attr('height', 20);
    this.drawDot(10, 8, '#000000');
  }

  checkShowDenovo(checked: boolean) {
    this.showDenovo = checked;

    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
    }
  }

  checkShowTransmitted(checked: boolean) {
    this.showTransmitted = checked;

    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
    }
  }

  checkEffectType(effectType: string, checked: boolean) {
    effectType = effectType.toLowerCase();
    if (checked) {
      this.selectedEffectTypes.push(effectType);
    } else {
      this.selectedEffectTypes.splice(this.selectedEffectTypes.indexOf(effectType), 1);
    }

    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
    }
  }

  getEffectVariantColor(worst_effect): string {
    worst_effect = worst_effect.toLowerCase();

    if (this.lgds.indexOf(worst_effect) !== -1 || worst_effect === 'lgds') {
      return '#ff0000';
    } else if (worst_effect === 'missense') {
      return '#ffff00';
    } else if (worst_effect === 'synonymous') {
      return '#69b3a2';
    } else {
      return '#555555';
    }
  }

  isVariantEffectSelected(worst_effect) {
    worst_effect = worst_effect.toLowerCase();

    if (this.selectedEffectTypes.indexOf(worst_effect) !== -1) {
      return true;
    }

    if (this.lgds.indexOf(worst_effect) !== -1) {
      if (this.selectedEffectTypes.indexOf('lgds') !== -1) {
        return true;
      }
    } else if (worst_effect !== 'missense' && worst_effect !== 'synonymous' && this.selectedEffectTypes.indexOf('other') !== -1) {
      return true;
    }
    return false;
  }

  frequencyIsSelected(frequency: number) {
    return frequency >= this.selectedFrequencies[0] && frequency <= this.selectedFrequencies[1];
  }

  toggleIntronCollapsing() {
    this.geneViewTranscript.collapseIntrons = !this.geneViewTranscript.collapseIntrons;
    this.setDefaultScale();
    this.drawGene();
    this.drawPlot();
  }

  filterSummaryVariantsArray(
    summaryVariantsArray: GeneViewSummaryVariantsArray, startPos: number, endPos: number
  ): GeneViewSummaryVariantsArray {
    const filteredVariants: GeneViewSummaryVariant[] = [];
    for (const summaryVariant of summaryVariantsArray.summaryVariants) {
      if (
        (!this.isVariantEffectSelected(summaryVariant.effect)) ||
        (!this.showDenovo && summaryVariant.seenAsDenovo) ||
        (!this.showTransmitted && !summaryVariant.seenAsDenovo)
      ) {
        continue;
      } else if (summaryVariant.position >= startPos && summaryVariant.position <= endPos) {
        if (this.frequencyIsSelected(summaryVariant.frequency)) {
          filteredVariants.push(summaryVariant);
        }
      }
    }
    return new GeneViewSummaryVariantsArray(filteredVariants.values());
  }

  filterTablePreviewVariantsArray(
    variantsArray: GenotypePreviewVariantsArray, startPos: number, endPos: number
  ): GenotypePreviewVariantsArray {
    const filteredVariants = [];
    const result = new GenotypePreviewVariantsArray();
    let location: string;
    let position: number;
    let frequency: string;
    for (const genotypePreview of variantsArray.genotypePreviews) {
      const data = genotypePreview.data;
      location = data.get(this.geneBrowserConfig.locationColumn);
      position = Number(location.slice(location.indexOf(':') + 1));
      frequency = data.get(this.geneBrowserConfig.frequencyColumn);
      if (!this.isVariantEffectSelected(data.get(this.geneBrowserConfig.effectColumn))) {
        continue;
      } else if (position >= startPos && position <= endPos) {
        if (frequency === '-') {
          frequency = '0.0';
        }
        if (this.frequencyIsSelected(Number(frequency))) {
          filteredVariants.push(genotypePreview);
        }
      }
    }
    result.setGenotypePreviews(filteredVariants);
    return result;
  }

  updateFamilyVariantsTable() {
    const filteredVariants = this.filterTablePreviewVariantsArray(
      this.variantsArray, this.x.domain()[0], this.x.domain()[this.x.domain().length - 1]
    );
    this.updateShownTablePreviewVariantsArrayEvent.emit(filteredVariants);
  }

  drawPlot() {
    const filteredSummaryVariants = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, this.x.domain()[0], this.x.domain()[this.x.domain().length - 1]
    );
    this.geneTableStats.selectedSummaryVariants = filteredSummaryVariants.summaryVariants.length;
    this.geneTableStats.selectedFamilyVariants = filteredSummaryVariants.summaryVariants.reduce(
      (a, b) => a + b.numberOfFamilyVariants, 0
    );

    if (this.gene !== undefined) {
      this.x_axis = d3.axisBottom(this.x);
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([this.frequencyDomainMin / 2.0]);
      this.y_axis_zero = d3.axisLeft(this.y_zero);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeightFreq})`).call(this.x_axis);
      this.svgElement.append('g').call(this.y_axis);
      this.svgElement.append('g').call(this.y_axis_subdomain);
      this.svgElement.append('g').call(this.y_axis_zero);

      for (const variant of filteredSummaryVariants.summaryVariants) {
        const color = this.getPhenoColor(variant);

        if (variant.isLGDs()) {
          this.drawStar(this.x(variant.position), this.getVariantY(variant.frequency), color);
        } else if (variant.isMissense()) {
          this.drawTriangle(this.x(variant.position), this.getVariantY(variant.frequency), color);
        } else if (variant.isSynonymous()) {
          this.drawCircle(this.x(variant.position), this.getVariantY(variant.frequency), color);
        } else {
          this.drawDot(this.x(variant.position), this.getVariantY(variant.frequency), color);
        }
        if (variant.seenAsDenovo) {
          this.drawSuroundingSquare(this.x(variant.position), this.getVariantY(variant.frequency), color);
        }
      }
    }
  }

  getPhenoColor(summaryVariant: GeneViewSummaryVariant): string {
    if (summaryVariant.seenInAffected) {
      if (summaryVariant.seenInUnaffected) {
        return '#AAAAAA';
      } else {
        return '#AA0000';
      }
    }
    return '#00AA00';
  }

  drawSuroundingSquare(x: number, y: number, color: string) {
    const w = 16;
    const h = 16;
    this.svgElement.append('g')
      .append('rect')
      .attr('x', x - w / 2)
      .attr('y', y - h / 2)
      .attr('width', w)
      .attr('height', h)
      .style('fill', color)
      .style('fill-opacity', 0.2)
      .style('stroke-width', 2)
      .style('stroke', color);
  }

  drawStar(x: number, y: number, color: string) {
    this.svgElement.append('svg')
    .attr('x', x - 8.5)
    .attr('y', y - 8.5)
    .append('g')
    .append('path')
    .attr('d', 'M12 .587l3.668 7.568 8.332 1.151-6.064 5.828 1.48 8.279-7.416-3.967-7.417 3.967 1.481-8.279-6.064-5.828 8.332-1.151z')
    .attr('transform', 'scale(0.7)')
    .attr('fill', color);
  }

  drawTriangle(x: number, y: number, color: string) {
    this.svgElement.append('g')
     .append('polygon')
     .attr('points', this.getTrianglePoints(x, y, 14))
     .style('stroke-width', 1)
     .style('stroke', color)
     .style('fill', color);
   }

  drawCircle(x: number, y: number, color: string) {
    this.svgElement.append('g')
    .append('circle')
    .attr('cx', x)
    .attr('cy', y)
    .attr('r', 7)
    .style('fill', color);
  }

  drawDot(x: number, y: number, color: string) {
    this.svgElement.append('g')
    .append('circle')
    .attr('cx', x)
    .attr('cy', y)
    .attr('r', 3)
    .style('fill', color);
  }

  drawTransmittedPlotVariant(variantInfo: GeneViewSummaryVariant) {
    this.svgElement.append('g')
      .append('circle')
      .attr('cx', this.x(variantInfo.position))
      .attr('cy', this.getVariantY(variantInfo.frequency))
      .attr('r', 5)
      .style('fill', this.getEffectVariantColor(variantInfo.effect));
  }

  drawDenovoPlotVariant(variantInfo: GeneViewSummaryVariant) {
    this.svgElement.append('g')
      .append('polygon')
      .attr('points', this.getTrianglePoints(
        this.x(variantInfo.position),
        this.getVariantY(variantInfo.frequency),
        15
      ))
      .style('stroke-width', 2)
      .style('stroke', '#000000')
      .style('fill', this.getEffectVariantColor(variantInfo.effect));
  }

  getVariantY(variantFrequency): number {
    let y: number;

    if (variantFrequency === 0) {
      y = this.y_zero('0');
    } else if (variantFrequency < this.frequencyDomainMin) {
      y = this.y_subdomain(variantFrequency);
    } else {
      y = this.y(variantFrequency);
    }

    return y;
  }

  getTrianglePoints(plotX: number, plotY: number, size: number) {
    const height = Math.sqrt(Math.pow(size, 2) - Math.pow((size / 2.0), 2));
    const x1 = plotX - (size / 2.0);
    const y1 = plotY + (height / 2.0);
    const x2 = plotX + (size / 2.0);
    const y2 = plotY + (height / 2.0);
    const x3 = plotX;
    const y3 = plotY - (height / 2.0);
    return `${x1},${y1} ${x2},${y2} ${x3},${y3}`;
  }

  setDefaultScale() {
    this.geneViewTranscript.resetStartStop();
    this.x.domain(GeneViewTranscript.domainFromSegments(this.geneViewTranscript.calculateSelectedSegments()));
    this.x.range(this.geneViewTranscript.calculatePlotRanges(this.svgWidth));
    this.selectedFrequencies = [0, this.frequencyDomainMax];
  }

  resetGeneTableValues(): void {
    this.geneTableStats = {
      geneSymbol: '',
      chromosome: '',
      totalFamilyVariants: 0,
      selectedFamilyVariants: 0,
      totalSummaryVariants: 0,
      selectedSummaryVariants: 0,
    };
  }

  // GENE VIEW FUNCTIONS
  drawGene() {
    this.svgHeight = this.svgHeightFreqRaw + this.gene.transcripts.length * 50;
    d3.select('#svg-container').selectAll('svg').remove();

    this.svgElement = d3.select('#svg-container')
      .append('svg')
      .attr('width', this.svgWidth + this.margin.left + this.margin.right)
      .attr('height', this.svgHeight)
      .append('g')
      .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);

    this.brush = d3.brush().extent([[0, 0], [this.svgWidth, this.svgHeightFreq]])
      .on('end', this.brushEndEvent);

    this.svgElement.append('g')
      .attr('class', 'brush')
      .call(this.brush);

    this.drawTranscript(this.svgHeightFreqRaw + 20);
    /**
    let transcriptYPosition = this.svgHeightFreqRaw + 20;
    for (let i = 0; i < this.gene.transcripts.length; i++) {
      this.drawTranscript(i, transcriptYPosition);
      transcriptYPosition += 50;
    }
    **/
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
      if (this.x.domain()[this.x.domain().length - 1] - this.x.domain()[0] > 12) {
        const newXmin = Math.round(this.x.invert(extent[0][0]));
        let newXmax = Math.round(this.x.invert(extent[1][0]));
        if (newXmax - newXmin < 12) {
          newXmax = newXmin + 12;
        }
        this.geneViewTranscript.start = newXmin;
        this.geneViewTranscript.stop = newXmax;
        this.x.domain(GeneViewTranscript.domainFromSegments(this.geneViewTranscript.calculateSelectedSegments()));
        this.x.range(this.geneViewTranscript.calculatePlotRanges(this.svgWidth));
        this.svgElement.select('.brush').call(this.brush.move, null);
      }

      // set new frequency limits
      const newFreqLimits = [
        this.convertBrushPointToFrequency(extent[0][1]),
        this.convertBrushPointToFrequency(extent[1][1])
      ];
      this.selectedFrequencies = [
        Math.min(...newFreqLimits),
        Math.max(...newFreqLimits),
      ];
    }

    this.drawGene();
    this.updateFamilyVariantsTable();
    this.drawPlot();
  }

  convertBrushPointToFrequency(brushY: number) {
    if (brushY < this.y_subdomain.range()[1]) {
      return this.y.invert(brushY);
    } else if (brushY < this.y_zero.range()[1]) {
      return this.y_subdomain.invert(brushY);
    } else {
      return 0;
    }
  }

  resetTimer = () => {
    this.doubleClickTimer = null;
  }

  drawTranscript(yPos: number) {
    const firstStart = this.geneViewTranscript.start;
    const strand = this.geneViewTranscript.transcript.strand;
    const totalExonCount = this.geneViewTranscript.transcript.exons.length;
    let i = 1;
    for (const segment of this.geneViewTranscript.calculateSelectedSegments()) {
      if (segment.isExon) {
        this.drawExon(segment.dnaStart, segment.dnaEnd, yPos, `exon ${i}/${totalExonCount}`, segment.isCDS);
      } else {
        this.drawIntron(segment.dnaStart, segment.dnaEnd, yPos, `intron ${i - 1}/${totalExonCount - 1}`);
      }
      i += 1;
    }
    this.drawTranscriptUTRText(
      this.geneViewTranscript.start, this.geneViewTranscript.stop, yPos, this.geneViewTranscript.transcript.strand
    );
  }

  drawExon(xStart: number, xEnd: number, y: number, title: string, cds: boolean) {
    let rectThickness = 10;
    if (cds) {
      rectThickness = 15;
      y -= 2.5;
      title = title + ' [CDS]';
    }
    this.drawRect(xStart, xEnd, y, rectThickness, title);
  }

  drawIntron(xStart: number, xEnd: number, y: number, title: string) {
    this.drawLine(xStart, xEnd, y, title);
  }

  drawTranscriptUTRText(xStart: number, xEnd: number, y: number, strand: string) {
    const UTR = { left: '5\'', right: '3\'' };

    if (strand === '-') {
      UTR.left = '3\'';
      UTR.right = '5\'';
    }

    this.svgElement.append('text')
      .attr('y', y + 10)
      .attr('x', this.x(xStart) - 20)
      .attr('font-size', '13px')
      .text(UTR.left)
      .attr('cursor', 'default')
      .append('svg:title').text(`UTR ${UTR.left}`);

    this.svgElement.append('text')
      .attr('y', y + 10)
      .attr('x', this.x(xEnd) + 10)
      .attr('font-size', '13px')
      .text(UTR.right)
      .attr('cursor', 'default')
      .append('svg:title').text(`UTR ${UTR.right}`);
  }

  drawRect(xStart: number, xEnd: number, y: number, height: number, svgTitle: string) {
    const width = this.x(xEnd) - this.x(xStart);

    this.svgElement.append('rect')
      .attr('height', height)
      .attr('width', width)
      .attr('x', this.x(xStart))
      .attr('y', y)
      .attr('stroke', 'rgb(0,0,0)')
      .append('svg:title').text(svgTitle);
  }

  drawLine(xStart: number, xEnd: number, y: number, svgTitle: string) {
    const xStartAligned = this.x(xStart);
    const xEndAligned = this.x(xEnd);

    this.svgElement.append('line')
      .attr('x1', xStartAligned)
      .attr('y1', y + 5)
      .attr('x2', xEndAligned)
      .attr('y2', y + 5)
      .attr('stroke', 'black')
      .append('svg:title').text(svgTitle);
  }
}
