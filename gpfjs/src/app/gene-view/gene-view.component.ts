import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import * as d3 from 'd3';
import { Gene, GeneViewSummaryVariantsArray, GeneViewSummaryVariant, DomainRange } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray, GenotypePreview } from 'app/genotype-preview-model/genotype-preview';
import { Subject } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Transcript, Exon } from 'app/gene-view/gene';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';



class GeneViewTranscriptSegment {

  private _start: number;
  private _stop: number;
  private _isExon: boolean;
  private _isCDS: boolean;
  private _label: string;

  constructor(
    start: number,
    stop: number,
    isExon: boolean,
    isCDS: boolean,
    label: string
  ) {
    this._start = start;
    this._stop = stop;
    this._isExon = isExon;
    this._isCDS = isCDS;
    this._label = label;
  }

  get start() {
    return this._start;
  }

  get stop() {
    return this._stop;
  }

  get length() {
    return this.stop - this.start;
  }

  get isExon() {
    return this._isExon;
  }

  get isIntron() {
    return !this._isCDS;
  }

  get isCDS() {
    return this._isCDS;
  }

  get label() {
    return this._label;
  }

  intersectionLength(min: number, max: number): number {
    const start = Math.max(this.start, min);
    const stop = Math.min(this.stop, max);

    if (start >= stop) {
      return 0;
    } else {
      return stop - start;
    }
  }

  isSubSegment(min: number, max: number): boolean {
    return this.start >= min && this.stop <= max;
  }
}

class GeneViewTranscript {

  transcript: Transcript;
  segments: GeneViewTranscriptSegment[] = [];

  get start() {
    return this.transcript.start;
  }

  get stop() {
    return this.transcript.stop;
  }

  get strand() {
    return this.transcript.strand;
  }

  constructor(transcript: Transcript) {
    this.transcript = transcript;

    const exonCount = this.transcript.exons.length;
    const intronCount = exonCount - 1;

    for (let i = 0; i < this.transcript.exons.length; i++) {
      const cdsTransition = this.getCDSTransitionPos(this.transcript.exons[i]);
      const segmentStart = this.transcript.exons[i].start;
      const segmentStop = this.transcript.exons[i].stop;
      if (cdsTransition) {
        // Split exons which are both inside and outside the coding region into two segments
        this.segments.push(
          new GeneViewTranscriptSegment(
            segmentStart, cdsTransition, true,
            this.isAreaInCDS(segmentStart, cdsTransition),
            `exon ${i + 1}/${exonCount}`),
          new GeneViewTranscriptSegment(
            cdsTransition, segmentStop, true,
            this.isAreaInCDS(cdsTransition, segmentStop),
            `exon ${i + 1}/${exonCount}`)
        );
      } else {
        this.segments.push(
          new GeneViewTranscriptSegment(
            segmentStart, segmentStop, true,
            this.isAreaInCDS(segmentStart, segmentStop),
            `exon ${i + 1}/${exonCount}`)
        );
      }
      // Add intron segment if applicable
      if (i + 1 < this.transcript.exons.length) {
        this.segments.push(
          new GeneViewTranscriptSegment(
            segmentStop, this.transcript.exons[i + 1].start,
            false, false, `intron ${i + 1}/${intronCount}`)
        );
      }
    }
  }

  isAreaInCDS(start: number, stop: number) {
    return (start >= this.transcript.cds[0]) && (stop <= this.transcript.cds[1]);
  }

  getCDSTransitionPos(exon: Exon) {
    const startIsInCDS = this.isAreaInCDS(exon.start, exon.start);
    const stopIsInCDS = this.isAreaInCDS(exon.stop, exon.stop);
    if (startIsInCDS !== stopIsInCDS) {
      return startIsInCDS ? this.transcript.cds[1] : this.transcript.cds[0];
    } else {
      return null;
    }
  }
}


class GeneViewModel {

  gene: Gene;
  rangeWidth: number;
  geneViewTranscripts: GeneViewTranscript[] = [];
  collapsedGeneViewTranscript: GeneViewTranscript;

  condensedRange: number[];
  condensedDomain: number[];
  normalDomain: number[];

  constructor(gene: Gene, rangeWidth: number) {
    this.gene = gene;
    this.rangeWidth = rangeWidth;

    for (const transcript of gene.transcripts) {
      this.geneViewTranscripts.push(new GeneViewTranscript(transcript));
    }

    this.collapsedGeneViewTranscript = new GeneViewTranscript(gene.collapsedTranscript());

    this.normalDomain = [
      this.collapsedGeneViewTranscript.start,
      this.collapsedGeneViewTranscript.stop
    ];

    this.condensedDomain = this.buildCondensedIntronsDomain(0, 3000000000);
    this.condensedRange = this.buildCondesedIntronsRange(0, 3000000000, this.rangeWidth);

  }

  buildCondensedIntronsDomain(domainMin: number, domainMax: number) {
    const domain: number[] = [];
    const filteredSegments = this.collapsedGeneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    const firstSegment = filteredSegments[0];
    if (firstSegment.isSubSegment(domainMin, domainMax)) {
      domain.push(firstSegment.start);
    } else {
      domain.push(domainMin);
    }
    for (let i = 1; i < filteredSegments.length; i++) {
      const segment = filteredSegments[i];
      domain.push(segment.start);
    }
    const lastSegment = filteredSegments[filteredSegments.length - 1];
    if (lastSegment.stop <= domainMax) {
      domain.push(lastSegment.stop);
    } else {
      domain.push(domainMax);
    }

    return domain;
  }

  buildCondesedIntronsRange(domainMin: number, domainMax: number, rangeWidth: number) {
    const range: number[] = [];
    const transcript = this.collapsedGeneViewTranscript.transcript;
    const filteredSegments = this.collapsedGeneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    const medianExonLength: number = transcript.medianExonLength;
    let condensedLength = 0;

    for (const segment of filteredSegments) {
      if (segment.isIntron) {
        const intronLength = segment.length;
        const intersectionLength = segment.intersectionLength(domainMin, domainMax);
        const factor = intersectionLength / intronLength;

        condensedLength += medianExonLength * factor;
      } else {
        const length = segment.intersectionLength(domainMin, domainMax);
        condensedLength += length;
      }
    }

    const scaleFactor: number = this.rangeWidth / condensedLength;

    let rollingTracker = 0;
    range.push(0);

    for (const segment of filteredSegments) {
      if (segment.isIntron) {
        const intronLength = segment.length;
        const intersectionLength = segment.intersectionLength(domainMin, domainMax);
        const factor = intersectionLength / intronLength;

        rollingTracker += medianExonLength * scaleFactor * factor;
      } else {
        rollingTracker += segment.intersectionLength(domainMin, domainMax) * scaleFactor;
      }
      range.push(rollingTracker);
    }
    return range;
  }
}

class GeneViewScaleState {
  constructor(
    public xDomain: number[],
    public xRange: number[],
    public yMin: number,
    public yMax: number,
  ) { }

  get xMin(): number {
    return this.xDomain[0];
  }

  get xMax(): number {
    return this.xDomain[this.xDomain.length - 1];
  }
}

class GeneViewZoomHistory {
  private zoomHistory: GeneViewScaleState[];
  private zoomHistoryIndex: number;

  constructor() {
    this.zoomHistory = [];
    this.zoomHistoryIndex = -1;
  }

  resetToDefaultState(defaultScale: GeneViewScaleState) {
    this.zoomHistory = [];
    this.zoomHistoryIndex = -1;
    this.append(defaultScale);
  }

  append(scale: GeneViewScaleState) {
    // If you append and the index is not in the end
    // clean the history after it and start apending new states
    this.zoomHistory = this.zoomHistory.slice(0, this.zoomHistoryIndex + 1);
    this.zoomHistory.push(scale);
    this.zoomHistoryIndex++;
  }

  moveToPrevious() {
    if (this.zoomHistoryIndex === 0) {
      return;
    }
    this.zoomHistoryIndex--;
  }

  moveToNext() {
    if (this.zoomHistoryIndex === this.zoomHistory.length - 1) {
      return;
    }
    this.zoomHistoryIndex++;
  }

  getState() {
    return this.zoomHistory[this.zoomHistoryIndex];
  }
}

@Component({
  selector: 'gpf-gene-view',
  templateUrl: './gene-view.component.html',
  styleUrls: ['./gene-view.component.css'],
  host: { '(document:keydown)': 'handleKeyboardEvent($event)' }
})
export class GeneViewComponent implements OnInit {
  @Input() gene: Gene;
  @Input() variantsArray: GeneViewSummaryVariantsArray;
  @Input() streamingFinished$: Subject<boolean>;
  @Output() updateShownTablePreviewVariantsArrayEvent = new EventEmitter<DomainRange>();

  geneBrowserConfig;
  frequencyDomainMin: number;
  frequencyDomainMax: number;
  condenseIntrons: boolean;

  summaryVariantsArray: GeneViewSummaryVariantsArray;

  options = {
    margin: { top: 10, right: 100, left: 100, bottom: 0 },
    axisScale: { domain: 0.90, subdomain: 0.05 },
    exonThickness: 14,
    cdsThickness: 20,
  };

  svgElement;
  summedTranscriptElement;
  transcriptsElement;
  svgWidth = 1200 - this.options.margin.left - this.options.margin.right;
  svgHeight;
  svgHeightFreqRaw = 400;
  svgHeightFreq = this.svgHeightFreqRaw - this.options.margin.top - this.options.margin.bottom;

  subdomainAxisY = Math.round(this.svgHeightFreq * this.options.axisScale.domain);
  zeroAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * this.options.axisScale.subdomain);

  lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  x;
  y;
  y_subdomain;
  y_zero;
  x_axis;
  y_axis;
  y_axis_subdomain;
  y_axis_zero;
  selectedEffectTypes = ['lgds', 'missense', 'synonymous', 'other'];
  selectedAffectedStatus = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
  selectedFrequencies;
  showDenovo = true;
  showTransmitted = true;

  geneViewModel: GeneViewModel;
  geneViewTranscript: GeneViewTranscript;

  brush;
  zoomHistory: GeneViewZoomHistory;
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
        .attr('width', this.svgWidth + this.options.margin.left + this.options.margin.right)
        .attr('height', this.svgHeightFreqRaw)
        .append('g')
        .attr('transform', `translate(${this.options.margin.left}, ${this.options.margin.top})`);

      this.summedTranscriptElement = this.svgElement
      .append('g');

      this.transcriptsElement = this.svgElement
      .append('g');

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
      this.summaryVariantsArray = this.variantsArray;

      this.condenseIntrons = false;
      this.setDefaultScale();

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

    this.zoomHistory = new GeneViewZoomHistory();
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.geneViewModel = new GeneViewModel(this.gene, this.svgWidth);
      this.geneViewTranscript = new GeneViewTranscript(this.gene.transcripts[0]);
      this.resetGeneTableValues();
      this.setDefaultScale();
      this.drawGene();
      this.zoomHistory.resetToDefaultState(this.calculateDefaultScale());
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
      this.updateFamilyVariantsTable();
    }
  }

  checkShowTransmitted(checked: boolean) {
    this.showTransmitted = checked;

    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
      this.updateFamilyVariantsTable();
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
      this.updateFamilyVariantsTable();
    }
  }

  checkAffectedStatus(affectedStatus: string, checked: boolean) {
    if (checked) {
      this.selectedAffectedStatus.push(affectedStatus);
    } else {
      this.selectedAffectedStatus.splice(this.selectedAffectedStatus.indexOf(affectedStatus), 1);
    }

    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
      this.updateFamilyVariantsTable();
    }
  }

  checkHideTranscripts(checked: boolean) {
    this.transcriptsElement.attr('display', checked ? 'none' : 'block');
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

  toggleCondenseIntron() {
    this.condenseIntrons = !this.condenseIntrons;
    this.setDefaultScale();
    this.drawGene();
    this.drawPlot();
    this.updateFamilyVariantsTable();
  }

  getAffectedStatusColor(affectedStatus: string): string {
    let color: string;

    if (affectedStatus === 'Affected only') {
      color = '#AA0000';
    } else if (affectedStatus === 'Unaffected only') {
      color = '#04613a';
    } else {
      color = '#8a8a8a';
    }

    return color;
  }

  getVariantAffectedStatus(summaryVariant: GeneViewSummaryVariant): string {
    let variantAffectedStatus: string;

    if (summaryVariant.seenInAffected) {
      if (summaryVariant.seenInUnaffected) {
        variantAffectedStatus = 'Affected and unaffected';
      } else {
        variantAffectedStatus = 'Affected only';
      }
    } else {
      variantAffectedStatus = 'Unaffected only';
    }

    return variantAffectedStatus;
  }

  isAffectedStatusSelected(affectedStatus: string): boolean {
    return this.selectedAffectedStatus.includes(affectedStatus) ? true : false;
  }

  filterSummaryVariantsArray(
    summaryVariantsArray: GeneViewSummaryVariantsArray, startPos: number, endPos: number
  ): GeneViewSummaryVariantsArray {
    const result = new GeneViewSummaryVariantsArray();
    for (const summaryVariant of summaryVariantsArray.summaryVariants) {
      if (
        (!this.isVariantEffectSelected(summaryVariant.effect)) ||
        (!this.showDenovo && summaryVariant.seenAsDenovo) ||
        (!this.showTransmitted && !summaryVariant.seenAsDenovo) ||
        (!this.isAffectedStatusSelected(this.getVariantAffectedStatus(summaryVariant)))
      ) {
        continue;
      } else if (summaryVariant.position >= startPos && summaryVariant.position <= endPos) {
        if (this.frequencyIsSelected(summaryVariant.frequency)) {
          result.push(summaryVariant);
        }
      }
    }
    return result;
  }

  getPedigreeAffectedStatus(pedigreeData): string {
    let result: string;
    let isInAffected = false;
    let isInUnaffected = false;

    for (const d of pedigreeData) {
      if (d.label > 0) {
        if (d.color === '#ffffff') {
          isInUnaffected = true;
        } else {
          isInAffected = true;
        }
      }
    }

    if (isInAffected && isInUnaffected) {
      result = 'Affected and unaffected';
    } else if (!isInAffected && isInUnaffected) {
      result = 'Unaffected only';
    } else {
      result = 'Affected only';
    }

    return result;
  }

  updateFamilyVariantsTable() {
    const currentState = this.zoomHistory.getState();
    const start = currentState.yMin;
    const end = currentState.yMax;
    const domains = new DomainRange(start, end);
    this.updateShownTablePreviewVariantsArrayEvent.emit(domains);
  }

  drawPlot() {
    const minDomain = this.x.domain()[0];
    const maxDomain = this.x.domain()[this.x.domain().length - 1];
    const domain = this.x.domain();
    const range = this.x.range();

    const filteredSummaryVariants = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, minDomain, maxDomain
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

      filteredSummaryVariants.summaryVariants.sort((a, b) => this.variantsComparator(a, b));

      for (const variant of filteredSummaryVariants.summaryVariants) {
        const color = this.getAffectedStatusColor(this.getVariantAffectedStatus(variant));
        const variantPosition = this.x(variant.position);

        if (variant.isLGDs()) {
          this.drawStar(variantPosition, this.getVariantY(variant.frequency), color);
        } else if (variant.isMissense()) {
          this.drawTriangle(variantPosition, this.getVariantY(variant.frequency), color);
        } else if (variant.isSynonymous()) {
          this.drawCircle(variantPosition, this.getVariantY(variant.frequency), color);
        } else {
          this.drawDot(variantPosition, this.getVariantY(variant.frequency), color);
        }
        if (variant.seenAsDenovo) {
          this.drawSuroundingSquare(variantPosition, this.getVariantY(variant.frequency), color);
        }
      }
    }
  }

  variantsComparator(a: GeneViewSummaryVariant, b: GeneViewSummaryVariant) {
    if (a.seenAsDenovo && !b.seenAsDenovo) {
      return 1;
    } else if (!a.seenAsDenovo && b.seenAsDenovo) {
      return -1;
    } else {
      if (a.isLGDs() && !b.isLGDs()) {
        return 1;
      } else if (!a.isLGDs() && b.isLGDs()) {
        return -1;
      } else if (a.isMissense() && !b.isMissense()) {
        return 1;
      } else if (!a.isMissense() && b.isMissense()) {
        return -1;
      } else if (a.isSynonymous() && !b.isSynonymous()) {
        return 1;
      } else if (!a.isSynonymous() && b.isSynonymous()) {
        return -1;
      } else {
        if (this.getVariantAffectedStatus(a) === 'Affected only' && this.getVariantAffectedStatus(b) !== 'Affected only') {
          return 1;
        } else if (this.getVariantAffectedStatus(a) !== 'Affected only' && this.getVariantAffectedStatus(b) === 'Affected only') {
          return -1;
        } else if (this.getVariantAffectedStatus(a) === 'Unaffected only' && this.getVariantAffectedStatus(b) !== 'Unaffected only') {
          return 1;
        } else if (this.getVariantAffectedStatus(a) !== 'Unaffected only' && this.getVariantAffectedStatus(b) === 'Unaffected only') {
          return -1;
        } else {
          return 0;
        }
      }
    }
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
      .style('stroke', color)
      .style('stroke-width', 2);
  }

  drawStar(x: number, y: number, color: string) {
    this.svgElement.append('svg')
      .attr('x', x - 8.5)
      .attr('y', y - 8.5)
      .append('g')
      .append('path')
      .attr('d', 'M12 .587l3.668 7.568 8.332 1.151-6.064 5.828 1.48 8.279-7.416-3.967-7.417 3.967 1.481-8.279-6.064-5.828 8.332-1.151z')
      .attr('transform', 'scale(0.7)')
      .attr('fill', color)
      .attr('fill-opacity', '0.6')
      .style('stroke-width', 1)
      .style('stroke', color);
  }

  drawTriangle(x: number, y: number, color: string) {
    this.svgElement.append('g')
      .append('polygon')
      .attr('points', this.getTrianglePoints(x, y, 14))
      .style('fill', color)
      .attr('fill-opacity', '0.6')
      .style('stroke-width', 1)
      .style('stroke', color);
  }

  drawCircle(x: number, y: number, color: string) {
    this.svgElement.append('g')
      .append('circle')
      .attr('cx', x)
      .attr('cy', y)
      .attr('r', 7)
      .style('fill', color)
      .attr('fill-opacity', '0.6')
      .style('stroke-width', 1)
      .style('stroke', color);
  }

  drawDot(x: number, y: number, color: string) {
    this.svgElement.append('g')
      .append('circle')
      .attr('cx', x)
      .attr('cy', y)
      .attr('r', 3)
      .style('fill', color)
      .attr('fill-opacity', '0.6')
      .style('stroke-width', 1)
      .style('stroke', color);
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
    const defaultScale = this.calculateDefaultScale();
    this.x = d3.scaleLinear().domain(defaultScale.xDomain).range(defaultScale.xRange).clamp(true);
    this.selectedFrequencies = [defaultScale.yMin, defaultScale.yMax];
  }

  calculateDefaultScale(): GeneViewScaleState {
    const domain = this.condenseIntrons ? this.geneViewModel.condensedDomain : this.geneViewModel.normalDomain;
    const range = this.condenseIntrons ? this.geneViewModel.condensedRange : [0, this.svgWidth];
    return new GeneViewScaleState(domain, range, 0, this.frequencyDomainMax);
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

  drawGene() {
    this.svgHeight = this.svgHeightFreqRaw + (this.gene.transcripts.length + 1) * 50;
    d3.select('#svg-container').selectAll('svg').remove();

    this.svgElement = d3.select('#svg-container')
      .append('svg')
      .attr('width', this.svgWidth + this.options.margin.left + this.options.margin.right)
      .attr('height', this.svgHeight)
      .append('g')
      .attr('transform', `translate(${this.options.margin.left}, ${this.options.margin.top})`);

    this.summedTranscriptElement = this.svgElement
    .append('g');

    this.transcriptsElement = this.svgElement
    .append('g');

    this.brush = d3.brush().extent([[0, 0], [this.svgWidth, this.svgHeightFreq]])
      .on('end', this.brushEndEvent);

    this.svgElement.append('g')
      .attr('class', 'brush')
      .call(this.brush);

    let transcriptY = this.svgHeightFreqRaw + 20;

    this.drawTranscript(this.summedTranscriptElement, transcriptY, this.geneViewModel.collapsedGeneViewTranscript);

    for (const geneViewTranscript of this.geneViewModel.geneViewTranscripts) {
      transcriptY += 50;
      this.drawTranscript(this.transcriptsElement, transcriptY, geneViewTranscript);
    }
  }

  brushEndEvent = () => {
    const extent = d3.event.selection;

    if (!extent) {
      if (!this.doubleClickTimer) {
        this.doubleClickTimer = setTimeout(this.resetTimer, 250);
        return;
      }

      this.zoomHistory.resetToDefaultState(this.calculateDefaultScale());
      this.setDefaultScale();
    } else {
      const x1 = extent[0][0];
      const x2 = extent[1][0];

      // set new frequency limits
      const newFreqLimits = [
        this.convertBrushPointToFrequency(extent[0][1]),
        this.convertBrushPointToFrequency(extent[1][1])
      ];

      let domain: number[];
      let range: number[];
      const domainMin = Math.round(this.x.invert(Math.min(x1, x2)));
      let domainMax = Math.round(this.x.invert(Math.max(x1, x2)));

      if (domainMax - domainMin < 12) {
        domainMax = domainMin + 12;
      }
      if (this.condenseIntrons) {
        domain = this.geneViewModel.buildCondensedIntronsDomain(
          domainMin, domainMax);
        range = this.geneViewModel.buildCondesedIntronsRange(
          domainMin, domainMax, this.svgWidth);
      } else {
        domain = [domainMin, domainMax];
        range = [0, this.svgWidth];
      }

      this.x = d3.scaleLinear().domain(domain).range(range).clamp(true);

      if (domainMax - domainMin >= 12) {
        this.zoomHistory.append(new GeneViewScaleState(domain, range, Math.min(...newFreqLimits), Math.max(...newFreqLimits)));
      }

      this.svgElement.select('.brush').call(this.brush.move, null);
      this.selectedFrequencies = [
        Math.min(...newFreqLimits),
        Math.max(...newFreqLimits),
      ];
    }

    this.drawGene();
    this.updateFamilyVariantsTable();
    this.drawPlot();
  }

  handleKeyboardEvent($event) {
    if ($event.ctrlKey && $event.key === 'z') {
      this.zoomHistory.moveToPrevious();
      this.drawFromHistory(this.zoomHistory.getState());
    }
    if ($event.ctrlKey && $event.key === 'y') {
      this.zoomHistory.moveToNext();
      this.drawFromHistory(this.zoomHistory.getState());
    }
  }

  drawFromHistory(scale: GeneViewScaleState) {
    this.x.domain(scale.xDomain);
    this.x.range(scale.xRange);
    this.selectedFrequencies = [
      scale.yMin,
      scale.yMax
    ];

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

  drawTranscript(element, yPos: number, geneViewTranscript: GeneViewTranscript) {
    const domain = this.x.domain();
    const domainMin = domain[0];
    const domainMax = domain[domain.length - 1];

    const segments = geneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    if (segments.length === 0) {
      return;
    }

    for (const segment of segments) {
      const start = Math.max(domainMin, segment.start);
      const stop = Math.min(domainMax, segment.stop);
      const xStart = this.x(start);
      const xStop = this.x(stop);

      if (segment.isExon) {
        this.drawExon(element, xStart, xStop, yPos, segment.label, segment.isCDS);
      } else {
        this.drawIntron(element, xStart, xStop, yPos, segment.label);
      }
    }

    const firstSegmentStart = Math.max(segments[0].start, domainMin);
    const lastSegmentStop = Math.min(segments[segments.length - 1].stop, domainMax);

    this.drawTranscriptUTRText(
      element,
      firstSegmentStart,
      lastSegmentStop,
      yPos, geneViewTranscript.strand
    );
  }

  drawExon(element, xStart: number, xEnd: number, y: number, title: string, cds: boolean) {
    let rectThickness = this.options.exonThickness;
    if (cds) {
      rectThickness = this.options.cdsThickness;
      y -= (rectThickness - this.options.exonThickness) / 2;
      title += ' [CDS]';
    }
    this.drawRect(element, xStart, xEnd, y, rectThickness, title);
  }

  drawIntron(element, xStart: number, xEnd: number, y: number, title: string) {
    this.drawLine(element, xStart, xEnd, y + this.options.exonThickness / 2, title);
  }

  drawTranscriptUTRText(element, xStart: number, xEnd: number, y: number, strand: string) {
    const UTR = { left: '5\'', right: '3\'' };

    if (strand === '-') {
      UTR.left = '3\'';
      UTR.right = '5\'';
    }

    element.append('text')
      .attr('y', y + 10)
      .attr('x', this.x(xStart) - 20)
      .attr('font-size', '13px')
      .text(UTR.left)
      .attr('cursor', 'default')
      .append('svg:title').text(`UTR ${UTR.left}`);

    element.append('text')
      .attr('y', y + 10)
      .attr('x', this.x(xEnd) + 10)
      .attr('font-size', '13px')
      .text(UTR.right)
      .attr('cursor', 'default')
      .append('svg:title').text(`UTR ${UTR.right}`);
  }

  drawTranscriptChromosomeText(element, xStart: number, y: number, chromosome: string) {
    element.append('text')
      .attr('y', y + 10)
      .attr('x', this.x(xStart) - 50)
      .attr('font-size', '13px')
      .text(`${chromosome}`)
      .attr('cursor', 'default')
      .append('svg:title').text(`Chromosome: ${chromosome}`);
  }


  drawRect(element, xStart: number, xEnd: number, y: number, height: number, svgTitle: string) {
    element.append('rect')
      .attr('height', height)
      .attr('width', xEnd - xStart)
      .attr('x', xStart)
      .attr('y', y)
      .attr('stroke', 'rgb(0,0,0)')
      .append('svg:title').text(svgTitle);
  }

  drawLine(element, xStart: number, xEnd: number, y: number, svgTitle: string) {
    element.append('line')
      .attr('x1', xStart)
      .attr('y1', y)
      .attr('x2', xEnd)
      .attr('y2', y)
      .attr('stroke', 'black')
      .append('svg:title').text(svgTitle);
  }
}
