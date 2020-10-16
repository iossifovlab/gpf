import { Component, OnInit, Input, OnChanges, Output, EventEmitter } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray, GenotypePreview } from 'app/genotype-preview-model/genotype-preview';
import { Subject } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Transcript, Exon } from 'app/gene-view/gene';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { line } from 'd3';


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
    for (const pedigreeData of genotypePreview.get('genotype')) {
      if (pedigreeData.label > 0) {
        if (pedigreeData.color === '#ffffff') {
          result.seenInUnaffected = true;
        } else {
          result.seenInAffected = true;
        }
      }
    }

    result.svuid = result.location + ':' + result.variant;

    return result;
  }

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

  start: number;
  stop: number;
  isExon: boolean;
  isCDS: boolean;

  constructor(
    start: number,
    stop: number,
    isExon: boolean,
    isCDS: boolean
  ) {
    this.start = start;
    this.stop = stop;
    this.isExon = isExon;
    this.isCDS = isCDS;
  }

  get length() {
    return this.stop - this.start;
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
      const cdsTransition = this.getCDSTransitionPos(this.transcript.exons[i]);
      const segmentStart = this.transcript.exons[i].start;
      const segmentStop = this.transcript.exons[i].stop;
      if (cdsTransition) {
        // Separate exons both inside and outside the coding region into two segments
        this.transcriptSegments.push(
          new GeneViewTranscriptSegment(segmentStart, cdsTransition, true, this.isInCDS(segmentStart, cdsTransition)),
          new GeneViewTranscriptSegment(cdsTransition, segmentStop, true, this.isInCDS(cdsTransition, segmentStop))
        );
      } else {
        this.transcriptSegments.push(
          new GeneViewTranscriptSegment(segmentStart, segmentStop, true, this.isInCDS(segmentStart, segmentStop))
        );
      }
      // Add intron segment if applicable
      if (i + 1 < this.transcript.exons.length) {
        this.transcriptSegments.push(
          new GeneViewTranscriptSegment(segmentStop, this.transcript.exons[i + 1].start, false, false)
        );
      }
    }
  }

  static domainFromSegments(segments: GeneViewTranscriptSegment[]): number[] {
    const domain: number[] = [];
    for (let i = 0; i < segments.length; i++) {
      domain.push(segments[i].start, segments[i].stop);
    }
    return domain;
  }

  isInCDS(start: number, stop: number) {
    return (start >= this.transcript.cds[0]) && (stop <= this.transcript.cds[1]);
  }

  getCDSTransitionPos(exon: Exon) {
    const startIsInCDS = this.isInCDS(exon.start, exon.start);
    const stopIsInCDS = this.isInCDS(exon.stop, exon.stop);
    if (startIsInCDS !== stopIsInCDS) {
      return startIsInCDS ? this.transcript.cds[1] : this.transcript.cds[0];
    } else {
      return null;
    }
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
      if (segment.stop <= this.start || segment.start >= this.stop) {
        continue;
      }
      const start = Math.max(this.start, this.transcriptSegments[i].start);
      const stop = Math.min(this.stop, this.transcriptSegments[i].stop);

      newSegments.push(new GeneViewTranscriptSegment(
        start, stop, segment.isExon, segment.isCDS
      ));
    }
    return newSegments;
  }

  calculatePlotRanges(plotWidth: number): number[] {
    const selectedSegments = this.calculateSelectedSegments();
    const selectedExonSegments = selectedSegments.filter(segment => segment.isExon);
    const selectedIntronSegments = selectedSegments.filter(segment => !segment.isExon);

    const linearScale = d3.scaleLinear()
    .domain([selectedSegments[0].start, selectedSegments[selectedSegments.length - 1].stop])
    .range([0, plotWidth]);

    let newIntronSpace = 0;
    for (let i = 0; i < selectedIntronSegments.length; i++) {
      let intronLength = selectedIntronSegments[i].stop - selectedIntronSegments[i].start;
      if (this.collapseIntrons) {
        intronLength = this.collapsedIntronLength;
      }
      newIntronSpace += intronLength;
    }

    const exonSpace = selectedExonSegments.reduce((a, b) => a + b.stop - b.start, 0);
    const newExonSpace = selectedSegments[selectedSegments.length - 1].stop - selectedSegments[0].start - newIntronSpace;
    const newExonRatio = newExonSpace / exonSpace;

    const plotSegments: number[] = [];
    let rollingPosTracker = 0;
    for (let i = 0; i < selectedSegments.length; i++) {
      let segmentLength = selectedSegments[i].stop - selectedSegments[i].start;
      if (selectedSegments[i].isExon) {
        segmentLength *= newExonRatio;
      } else if (this.collapseIntrons) {
        segmentLength = this.collapsedIntronLength;
      }
      segmentLength = linearScale(linearScale.domain()[0] + segmentLength);
      plotSegments.push(
        rollingPosTracker, rollingPosTracker + segmentLength
      );
      rollingPosTracker += segmentLength;
    }
    return plotSegments;
  }
}

class CollapsedSegments {

  transcriptSegments: GeneViewTranscriptSegment[];
  transcriptSegmentsCollapsed: GeneViewTranscriptSegment[] = [];
  collapseIntrons: boolean;
  collapsedIntronLength: number; // in base pairs, not px

  constructor(transcriptSegments: GeneViewTranscriptSegment[], collapseIntrons: boolean, collapsedIntronLength: number) {
    this.collapseIntrons = collapseIntrons;
    this.collapsedIntronLength = collapsedIntronLength;
    this.transcriptSegments = transcriptSegments;

    let rollingPosTracker = 0;
    for (const segment of transcriptSegments) {
      const segmentLength = segment.isExon ? segment.length : collapsedIntronLength;
      this.transcriptSegmentsCollapsed.push(
        new GeneViewTranscriptSegment(rollingPosTracker, rollingPosTracker + segmentLength, segment.isExon, segment.isCDS)
      );
      rollingPosTracker += segmentLength;
    }
  }

  getSegmentIndex(coordinateSystem: boolean, coordinate: number): number {
    /**
      coordinateSystem:
      -> 0 indicates the real coordinate system (i.e. DNA positions)
      -> 1 indicates the pseudo coordinate system (with collapsed introns)
    **/
    const segments: GeneViewTranscriptSegment[] = coordinateSystem ? this.transcriptSegmentsCollapsed : this.transcriptSegments;
    for (let i = 0; i < segments.length; i++) {
      if (segments[i].start <= coordinate && coordinate <= segments[i].stop) {
        return i;
      }
    }
    return -1;
  }

  convertCoordinate(coordinateSystem: boolean, coordinate: number): number {
    const segments: GeneViewTranscriptSegment[] = coordinateSystem ? this.transcriptSegmentsCollapsed : this.transcriptSegments;
    const targetSegments: GeneViewTranscriptSegment[] = coordinateSystem ? this.transcriptSegments : this.transcriptSegmentsCollapsed;
    const segmentIndex = this.getSegmentIndex(coordinateSystem, coordinate);
    if (segmentIndex !== -1) {
      return targetSegments[segmentIndex].start + Math.round(((coordinate - segments[segmentIndex].start) / segments[segmentIndex].length) * (targetSegments[segmentIndex].length));
    } else {
      return coordinate;
    }
  }

  getDomain(coordinateSystem: boolean): number[] {
    const segments: GeneViewTranscriptSegment[] = coordinateSystem ? this.transcriptSegmentsCollapsed : this.transcriptSegments;
    return [segments[0].start, segments[segments.length - 1].stop];
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
  selectedAffectedStatus = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
  selectedFrequencies;
  showDenovo = true;
  showTransmitted = true;

  geneViewTranscript: GeneViewTranscript;
  collapsedSegments: CollapsedSegments;

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
      this.collapsedSegments = new CollapsedSegments(this.geneViewTranscript.transcriptSegments, false, 200);
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
    this.collapsedSegments.collapseIntrons = !this.collapsedSegments.collapseIntrons;
    this.setDefaultScale();
    this.drawGene();
    this.drawPlot();
  }

  getAffectedStatusColor(affectedStatus: string): string {
    let color: string;

    if (affectedStatus === 'Affected only') {
      color = '#AA0000';
    } else if (affectedStatus === 'Unaffected only') {
      color = '#00AA00';
    } else {
      color = '#AAAAAA';
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
    const filteredVariants: GeneViewSummaryVariant[] = [];
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
      if (
        (!this.isVariantEffectSelected(data.get(this.geneBrowserConfig.effectColumn))) ||
        (!this.showDenovo && data.get('variant.is denovo')) ||
        (!this.showTransmitted && !data.get('variant.is denovo'))
      ) {
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

    let minDomain = this.x.domain()[0];
    let maxDomain = this.x.domain()[this.x.domain().length - 1];
    if (this.collapsedSegments.collapseIntrons) {
      minDomain = this.collapsedSegments.convertCoordinate(
        this.collapsedSegments.collapseIntrons, minDomain
      );
      maxDomain = this.collapsedSegments.convertCoordinate(
        this.collapsedSegments.collapseIntrons, maxDomain
      );
    }

    const filteredSummaryVariants = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, minDomain, maxDomain
    );
    this.geneTableStats.selectedSummaryVariants = filteredSummaryVariants.summaryVariants.length;
    this.geneTableStats.selectedFamilyVariants = filteredSummaryVariants.summaryVariants.reduce(
      (a, b) => a + b.numberOfFamilyVariants, 0
    );

    if (this.gene !== undefined) {
      this.x_axis = d3.axisBottom(this.x).tickFormat(
        x => String(this.collapsedSegments.collapseIntrons ? this.collapsedSegments.convertCoordinate(true, +x) : +x)
      );
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([this.frequencyDomainMin / 2.0]);
      this.y_axis_zero = d3.axisLeft(this.y_zero);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeightFreq})`).call(this.x_axis);
      this.svgElement.append('g').call(this.y_axis);
      this.svgElement.append('g').call(this.y_axis_subdomain);
      this.svgElement.append('g').call(this.y_axis_zero);

      for (const variant of filteredSummaryVariants.summaryVariants) {
        const color = this.getAffectedStatusColor(this.getVariantAffectedStatus(variant));

        let variantPosition;
        if (this.collapsedSegments.collapseIntrons) {
          variantPosition = this.collapsedSegments.convertCoordinate(
            false, variant.position
          );
        } else {
          variantPosition = variant.position;
        }
        variantPosition = this.x(variantPosition);

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
      .attr('cx', this.x(this.collapsedSegments.convertCoordinate(this.collapsedSegments.collapseIntrons, variantInfo.position)))
      .attr('cy', this.getVariantY(variantInfo.frequency))
      .attr('r', 5)
      .style('fill', this.getEffectVariantColor(variantInfo.effect));
  }

  drawDenovoPlotVariant(variantInfo: GeneViewSummaryVariant) {
    this.svgElement.append('g')
      .append('polygon')
      .attr('points', this.getTrianglePoints(
        this.x(this.collapsedSegments.convertCoordinate(this.collapsedSegments.collapseIntrons, variantInfo.position)),
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
    this.x.domain(this.collapsedSegments.getDomain(this.collapsedSegments.collapseIntrons));
    this.x.range([0, this.svgWidth]);
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
        this.x.domain([newXmin, newXmax]);
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
    const totalExonCount = this.geneViewTranscript.transcript.exons.length;
    let i = 1;
    const segments = this.collapsedSegments.collapseIntrons ?
      this.collapsedSegments.transcriptSegmentsCollapsed : this.collapsedSegments.transcriptSegments;
    for (const segment of segments) {
      if (segment.isExon) {
        this.drawExon(segment.start, segment.stop, yPos, `exon ${i}/${totalExonCount}`, segment.isCDS);
      } else {
        this.drawIntron(segment.start, segment.stop, yPos, `intron ${i - 1}/${totalExonCount - 1}`);
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
