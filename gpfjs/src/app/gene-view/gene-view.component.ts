import { Component, OnInit, Input, Output, EventEmitter, forwardRef } from '@angular/core';
import * as d3 from 'd3';
import { Gene, GeneViewSummaryVariantsArray, GeneViewSummaryVariant, DomainRange } from 'app/gene-view/gene';
import { Subject, Observable } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { drawRect, drawLine, drawHoverText, drawStar, drawCircle, drawTriangle, drawSurroundingSquare, drawDot } from 'app/utils/svg-drawing';
import { GeneViewTranscript, GeneViewModel } from 'app/gene-view/gene-view';
import { QueryStateProvider, QueryStateWithErrorsProvider } from 'app/query/query-state-provider';


class GeneViewScaleState {
  constructor(
    public xDomain: number[],
    public xRange: number[],
    public yMin: number,
    public yMax: number,
    public condenseToggled: boolean,
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

  get currentState() {
    return this.zoomHistory[this.zoomHistoryIndex];
  }

  get canGoForward() {
    return this.zoomHistoryIndex < this.zoomHistory.length - 1;
  }

  get canGoBackward() {
    return this.zoomHistoryIndex > 0;
  }

  resetToDefaultState(defaultScale: GeneViewScaleState) {
    this.zoomHistory = [];
    this.zoomHistoryIndex = -1;
    this.addStateToHistory(defaultScale);
  }

  addStateToHistory(scale: GeneViewScaleState) {
    // If you append and the index is not in the end
    // clean the history after it and start apending new states
    this.zoomHistory = this.zoomHistory.slice(0, this.zoomHistoryIndex + 1);
    this.zoomHistory.push(scale);
    this.zoomHistoryIndex++;
  }

  moveToPrevious() {
    if (this.canGoBackward) {
      this.zoomHistoryIndex--;
    }
  }

  moveToNext() {
    if (this.canGoForward) {
      this.zoomHistoryIndex++;
    }
  }
}

@Component({
  selector: 'gpf-gene-view',
  templateUrl: './gene-view.component.html',
  styleUrls: ['./gene-view.component.css'],
  host: { '(document:keydown)': 'handleKeyboardEvent($event)' },
  providers: [{ provide: QueryStateProvider, useExisting: forwardRef(() => GeneViewComponent) }]
})
export class GeneViewComponent extends QueryStateWithErrorsProvider implements OnInit {
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
    margin: { top: 10, right: 50, left: 180, bottom: 0 },
    axisScale: { domain: 0.90, subdomain: 0.05 },
    exonThickness: { normal: 6.25, collapsed: 12.5 },
    cdsThickness: { normal: 12.5, collapsed: 25 },
    xAxisTicks: 12,
  };

  svgElement;
  summedTranscriptElement;
  transcriptsElement;
  svgWidth;
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
  fontSize: number;
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
  ) {
    super();
  }

  ngOnInit() {
    this.fontSize = this.calculateTextFontSize(window.innerWidth);
    this.svgWidth = window.innerWidth - this.options.margin.left - this.options.margin.right;

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
      this.setDefaultScale();
      this.resetGeneTableValues();
      this.drawGene();
    }
  }

  getState(): Observable<object> {
    const state = {
      'affectedStatus': Array.from(this.selectedAffectedStatus),
      'selectedEffectTypes': Array.from(this.selectedEffectTypes),
      'zoomState': this.zoomHistory.currentState,
      'showDenovo': this.showDenovo,
      'showTransmitted': this.showTransmitted
    };
    return this.validateAndGetState(state);
  }

  enableIntronCondensing() {
    this.condenseIntrons = true;
  }

  disableIntronCondensing() {
    this.condenseIntrons = false;
  }

  drawTransmittedIcons() {
    this.svgElement = d3.select('#transmitted')
      .attr('width', 80)
      .attr('height', 20);
    drawStar(this.svgElement, 10, 7.5, '#000000');
    drawTriangle(this.svgElement, 30, 8, '#000000');
    drawCircle(this.svgElement, 50, 8, '#000000');
    drawDot(this.svgElement, 70, 8, '#000000');
  }

  drawDenovoIcons() {
    this.svgElement = d3.select('#denovo')
      .attr('width', 80)
      .attr('height', 20);
    drawStar(this.svgElement, 10, 7.5, '#000000');
    drawSurroundingSquare(this.svgElement, 10, 7.5, '#000000');
    drawTriangle(this.svgElement, 30, 8, '#000000');
    drawSurroundingSquare(this.svgElement, 30, 8, '#000000');
    drawCircle(this.svgElement, 50, 8, '#000000');
    drawSurroundingSquare(this.svgElement, 50, 8, '#000000');
    drawDot(this.svgElement, 70, 8, '#000000');
    drawSurroundingSquare(this.svgElement, 70, 8, '#000000');
  }

  drawEffectTypesIcons() {
    const effectIcons = {
      '#LGDs': drawStar,
      '#Missense': drawTriangle,
      '#Synonymous': drawCircle,
      '#Other': drawDot
    };
    for (const [effect, draw] of Object.entries(effectIcons)) {
      this.svgElement = d3.select(effect)
        .attr('width', 20)
        .attr('height', 20);
      draw(this.svgElement, 10, 8, '#000000');
    }
  }

  redraw() {
    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
      this.updateFamilyVariantsTable(); // TODO see if this can't be removed from here, causes a request
    }
  }

  checkShowDenovo(checked: boolean) {
    this.showDenovo = checked;
    this.redraw();
  }

  checkShowTransmitted(checked: boolean) {
    this.showTransmitted = checked;
    this.redraw();
  }

  checkEffectType(effectType: string, checked: boolean) {
    effectType = effectType.toLowerCase();
    if (checked) {
      this.selectedEffectTypes.push(effectType);
    } else {
      this.selectedEffectTypes.splice(this.selectedEffectTypes.indexOf(effectType), 1);
    }
    this.redraw();
  }

  checkAffectedStatus(affectedStatus: string, checked: boolean) {
    if (checked) {
      this.selectedAffectedStatus.push(affectedStatus);
    } else {
      this.selectedAffectedStatus.splice(this.selectedAffectedStatus.indexOf(affectedStatus), 1);
    }
    this.redraw();
  }

  checkHideTranscripts(checked: boolean) {
    const height = this.svgHeightFreqRaw + 85;
    const heightWithTranscripts = height + (this.gene.transcripts.length + 1) * 25;

    if (checked) {
      this.transcriptsElement.attr('display', 'none');
      d3.select('#svg-container svg')
      .attr('viewBox', '0 0 ' + (this.svgWidth + this.options.margin.left + this.options.margin.right).toString() +
      ' ' + height.toString());
    } else {
      this.transcriptsElement.attr('display', 'block');
      d3.select('#svg-container svg')
      .attr('viewBox', '0 0 ' + (this.svgWidth + this.options.margin.left + this.options.margin.right).toString() +
      ' ' + heightWithTranscripts.toString());
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

  toggleCondenseIntron() {
    let domain;
    let range;
    const domainMin = this.x.domain()[0];
    const domainMax = this.x.domain()[this.x.domain().length - 1];
    this.condenseIntrons = !this.condenseIntrons;
    domain = this.geneViewModel.buildDomain(domainMin, domainMax);
    if (this.condenseIntrons) {
      range = this.geneViewModel.buildCondensedIntronsRange(domainMin, domainMax);
    } else {
      range = this.geneViewModel.buildNormalIntronsRange(domainMin, domainMax);
    }

    this.zoomHistory.addStateToHistory(
      new GeneViewScaleState(domain, range, this.selectedFrequencies[0], this.selectedFrequencies[1], this.condenseIntrons)
    );
    this.x.domain(domain);
    this.x.range(range);
    this.redraw();
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
    const start = this.zoomHistory.currentState.yMin;
    const end = this.zoomHistory.currentState.yMax;
    const domains = new DomainRange(start, end);
    this.updateShownTablePreviewVariantsArrayEvent.emit(domains);
  }

  drawPlot() {
    const minDomain = this.x.domain()[0];
    const maxDomain = this.x.domain()[this.x.domain().length - 1];

    const filteredSummaryVariants = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, minDomain, maxDomain
    );
    this.geneTableStats.selectedSummaryVariants = filteredSummaryVariants.summaryVariants.length;
    this.geneTableStats.selectedFamilyVariants = filteredSummaryVariants.summaryVariants.reduce(
      (a, b) => a + b.numberOfFamilyVariants, 0
    );

    if (this.gene !== undefined) {
      this.x_axis = d3.axisBottom(this.x).tickValues(this.calculateTranscriptAxisTicks(this.geneViewModel.collapsedGeneViewTranscript));
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([this.frequencyDomainMin / 2.0]);
      this.y_axis_zero = d3.axisLeft(this.y_zero);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeightFreq})`).call(this.x_axis).style('font', `${this.fontSize}px sans-serif`);
      this.svgElement.append('g').call(this.y_axis).style('font', `${this.fontSize}px sans-serif`);
      this.svgElement.append('g').call(this.y_axis_subdomain).style('font', `${this.fontSize}px sans-serif`);
      this.svgElement.append('g').call(this.y_axis_zero).style('font', `${this.fontSize}px sans-serif`);

      filteredSummaryVariants.summaryVariants.sort((a, b) => GeneViewSummaryVariant.comparator(a, b));

      for (const variant of filteredSummaryVariants.summaryVariants) {
        const color = this.getAffectedStatusColor(this.getVariantAffectedStatus(variant));
        const variantPosition = this.x(variant.position);

        if (variant.isLGDs()) {
          drawStar(this.svgElement, variantPosition, this.getVariantY(variant.frequency), color);
        } else if (variant.isMissense()) {
          drawTriangle(this.svgElement, variantPosition, this.getVariantY(variant.frequency), color);
        } else if (variant.isSynonymous()) {
          drawCircle(this.svgElement, variantPosition, this.getVariantY(variant.frequency), color);
        } else {
          drawDot(this.svgElement, variantPosition, this.getVariantY(variant.frequency), color);
        }
        if (variant.seenAsDenovo) {
          drawSurroundingSquare(this.svgElement, variantPosition, this.getVariantY(variant.frequency), color);
        }
      }
    }
  }

  getVariantY(variantFrequency: number): number {
    if (variantFrequency === 0) {
      return this.y_zero('0');
    } else if (variantFrequency < this.frequencyDomainMin) {
      return this.y_subdomain(variantFrequency);
    } else {
      return this.y(variantFrequency);
    }
  }

  convertBrushPointToFrequency(brushY: number): number {
    if (brushY < this.y_subdomain.range()[1]) {
      return this.y.invert(brushY);
    } else if (brushY < this.y_zero.range()[1]) {
      return this.y_subdomain.invert(brushY);
    } else {
      return 0;
    }
  }

  setDefaultScale() {
    const domain = this.geneViewModel.domain;
    const range = this.condenseIntrons ? this.geneViewModel.condensedRange : this.geneViewModel.normalRange;
    const defaultScale = new GeneViewScaleState(domain, range, 0, this.frequencyDomainMax, this.condenseIntrons);
    this.x = d3.scaleLinear().domain(domain).range(range).clamp(true);
    this.selectedFrequencies = [0, this.frequencyDomainMax];
    this.zoomHistory.resetToDefaultState(defaultScale);
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
    this.svgHeight = this.svgHeightFreqRaw + (this.gene.transcripts.length + 1) * 25 + 70;
    d3.select('#svg-container').selectAll('svg').remove();

    this.svgElement = d3.select('#svg-container')
      .append('svg')
      .attr('viewBox', '0 0 ' + (this.svgWidth + this.options.margin.left + this.options.margin.right).toString() +
          ' ' + (this.svgHeightFreqRaw + 85 + (this.gene.transcripts.length + 1) * 25).toString())
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

    let transcriptY = this.svgHeightFreqRaw + 30;
    this.drawTranscript(this.summedTranscriptElement, transcriptY, this.geneViewModel.collapsedGeneViewTranscript);
    transcriptY += 25;
    for (const geneViewTranscript of this.geneViewModel.geneViewTranscripts) {
      transcriptY += 25;
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

      domain = this.geneViewModel.buildDomain(domainMin, domainMax);
      if (this.condenseIntrons) {
        range = this.geneViewModel.buildCondensedIntronsRange(domainMin, domainMax);
      } else {
        range = this.geneViewModel.buildNormalIntronsRange(domainMin, domainMax);
      }

      this.x = d3.scaleLinear().domain(domain).range(range).clamp(true);

      if (domainMax - domainMin >= 12) {
        this.zoomHistory.addStateToHistory(
          new GeneViewScaleState(domain, range, Math.min(...newFreqLimits), Math.max(...newFreqLimits), this.condenseIntrons)
        );
      }

      this.svgElement.select('.brush').call(this.brush.move, null);
      this.selectedFrequencies = [
        Math.min(...newFreqLimits),
        Math.max(...newFreqLimits),
      ];
    }
    this.redraw();
  }

  historyUndo() {
    this.zoomHistory.moveToPrevious();
    this.drawFromHistory(this.zoomHistory.currentState);
  }

  historyRedo() {
    this.zoomHistory.moveToNext();
    this.drawFromHistory(this.zoomHistory.currentState);
  }

  handleKeyboardEvent($event) {
    if ($event.ctrlKey && $event.key === 'z') {
      this.historyUndo();
    }
    if ($event.ctrlKey && $event.key === 'y') {
      this.historyRedo();
    }
  }

  drawFromHistory(scale: GeneViewScaleState) {
    this.x.domain(scale.xDomain);
    this.x.range(scale.xRange);
    this.selectedFrequencies = [scale.yMin, scale.yMax];
    this.condenseIntrons = scale.condenseToggled;
    this.redraw();
  }

  resetTimer = () => {
    this.doubleClickTimer = null;
  }

  getSelectedChromosomes(geneViewTranscript: GeneViewTranscript) {
    const domain = this.x.domain();
    const domainMin = domain[0];
    const domainMax = domain[domain.length - 1];
    const selectedChromosomes = {};
    for (const [chromosome, range] of Object.entries(geneViewTranscript.chromosomes)) {
      if (range[1] < domainMin || range[0] > domainMax) {
        continue;
      } else {
        selectedChromosomes[chromosome] = range;
      }
    }
    return selectedChromosomes;
  }

  drawChromosomeLabels(element, yPos: number, geneViewTranscript: GeneViewTranscript) {
    const domain = this.x.domain();
    const domainMin = domain[0];
    const domainMax = domain[domain.length - 1];
    const chromosomes = this.getSelectedChromosomes(geneViewTranscript);
    let from: number;
    let to: number;
    for (const [chromosome, range] of Object.entries(chromosomes)) {
      from = Math.max(range[0], domainMin);
      to = Math.min(range[1], domainMax);
      drawHoverText(element, this.x((from + to) / 2) - 43, yPos + 35, `Chromosome: ${chromosome}`, '', this.fontSize);
    }
  }

  calculateTranscriptAxisTicks(geneViewTranscript: GeneViewTranscript) {
    const domain = this.x.domain();
    const domainMin = domain[0];
    const domainMax = domain[domain.length - 1];
    const chromosomes = this.getSelectedChromosomes(geneViewTranscript);
    const ticks = [];
    let from: number;
    let to: number;

    for (const [chromosome, range] of Object.entries(chromosomes)) {
      from = this.x(Math.max(range[0], domainMin));
      to = this.x(Math.min(range[1], domainMax));
      const increment = (to - from) / (this.options.xAxisTicks / Object.keys(chromosomes).length);
      for (let i = from; i < to; i += increment) {
        ticks.push(this.x.invert(i));
      }
      if (ticks[ticks.length - 1] !== this.x.invert(to)) {
        ticks.push(this.x.invert(to));
      }
    }
    return ticks;
  }

  calculateTextFontSize(screenWidth: number) {
    let fontSize: number;

    if (screenWidth < 1300) {
      fontSize = 12;
    } else if (screenWidth > 2000) {
      fontSize = 15;
    } else {
      fontSize = 12 + ((screenWidth - 1300) / 233);
    }

    return fontSize;
  }

  drawTranscript(element, yPos: number, geneViewTranscript: GeneViewTranscript) {
    const domain = this.x.domain();
    const domainMin = domain[0];
    const domainMax = domain[domain.length - 1];
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
      nonCoding: this.options.exonThickness.normal,
      coding: this.options.cdsThickness.normal
    };

    if (transcriptId === 'collapsed') {
      brushSize = { nonCoding: this.options.exonThickness.collapsed, coding: this.options.cdsThickness.collapsed };
      this.drawChromosomeLabels(element, yPos, geneViewTranscript);
    } else {
      drawHoverText(element, this.x(firstSegmentStart) - 150, yPos + 10, transcriptId, 'Transcript id: ', this.fontSize);
    }

    this.drawTranscriptUTRText(element, firstSegmentStart, lastSegmentStop, yPos, geneViewTranscript.strand);

    for (const segment of segments) {
      const start = Math.max(domainMin, segment.start);
      const stop = Math.min(domainMax, segment.stop);
      const xStart = this.x(start);
      const xStop = this.x(stop);

      if (segment.isExon) {
        this.drawExon(element, xStart, xStop, yPos, segment.label, segment.isCDS, brushSize);
      } else if (!segment.isSpacer) {
        this.drawIntron(element, xStart, xStop, yPos, segment.label, brushSize);
      }
    }
  }

  drawExon(element, xStart: number, xEnd: number, y: number, title: string, cds: boolean, brushSize) {
    let rectThickness = brushSize.nonCoding;
    if (cds) {
      rectThickness = brushSize.coding;
      y -= (brushSize.coding - brushSize.nonCoding) / 2;
      title += ' [CDS]';
    }
    drawRect(element, xStart, xEnd, y, rectThickness, title);
  }

  drawIntron(element, xStart: number, xEnd: number, y: number, title: string, brushSize) {
    drawLine(element, xStart, xEnd, y + brushSize.nonCoding / 2, title);
  }

  drawTranscriptUTRText(element, xStart: number, xEnd: number, y: number, strand: string) {
    const UTR = { left: '5\'', right: '3\'' };
    if (strand === '-') {
      UTR.left = '3\'';
      UTR.right = '5\'';
    }
    drawHoverText(element, this.x(xStart) - 20, y + 10, UTR.left, 'UTR ', this.fontSize);
    drawHoverText(element, this.x(xEnd) + 10, y + 10, UTR.right, 'UTR ', this.fontSize);
  }
}
