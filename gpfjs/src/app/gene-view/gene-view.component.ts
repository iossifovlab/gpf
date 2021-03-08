import { Component, OnInit, Input, Output, EventEmitter, forwardRef, ViewChild, ViewChildren } from '@angular/core';
import * as d3 from 'd3';
import { Gene, GeneViewSummaryVariantsArray, GeneViewSummaryAllele, DomainRange, GeneViewSummaryVariant } from 'app/gene-view/gene';
import { Subject, Observable } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import * as draw from 'app/utils/svg-drawing';
import { GeneViewTranscript, GeneViewModel } from 'app/gene-view/gene-view';
import { QueryStateProvider, QueryStateWithErrorsProvider } from 'app/query/query-state-provider';

export class GeneViewScaleState {
  constructor(
    public xDomain: number[],
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

export class GeneViewZoomHistory {
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
  host: {
    '(document:keydown)': 'handleKeyboardEvent($event)',
    '(window:resize)': 'handleWindowResizeEvent($event)'
  },
  providers: [{ provide: QueryStateProvider, useExisting: forwardRef(() => GeneViewComponent) }]
})
export class GeneViewComponent extends QueryStateWithErrorsProvider implements OnInit {
  @Input() gene: Gene;
  @Input() variantsArray: GeneViewSummaryVariantsArray;
  @Input() streamingFinished$: Subject<boolean>;
  @Output() updateShownTablePreviewVariantsArrayEvent = new EventEmitter<DomainRange>();
  @ViewChildren('affectedStatusCheckbox') affectedStatusCheckboxes;
  @ViewChildren('effectTypeCheckbox') effectTypeCheckboxes;
  @ViewChild('denovoCheckbox') denovoCheckbox;
  @ViewChild('transmittedCheckbox') transmittedCheckbox;
  @ViewChildren('variantTypeCheckbox') variantTypeCheckboxes;

  geneBrowserConfig;
  frequencyDomainMin: number;
  frequencyDomainMax: number;
  condenseIntrons: boolean;

  summaryVariantsArray: GeneViewSummaryVariantsArray;
  filteredSummaryVariantsArray: GeneViewSummaryVariantsArray = new GeneViewSummaryVariantsArray();

  options = {
    margin: { top: 10, right: 50, left: 140, bottom: 0 },
    axisScale: { domain: 0.90, subdomain: 0.05 },
    exonThickness: { normal: 6.25, collapsed: 12.5 },
    cdsThickness: { normal: 12.5, collapsed: 25 },
    xAxisTicks: 13,
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
  yAxisLabel;
  fontSize: number;
  selectedEffectTypes = ['lgds', 'missense', 'synonymous', 'cnv+', 'cnv-', 'other'];
  selectedVariantTypes = ['sub', 'ins', 'del', 'cnv+', 'cnv-'];
  selectedAffectedStatus = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
  selectedFrequencies;
  showDenovo = true;
  showTransmitted = true;

  geneViewModel: GeneViewModel;
  geneViewTranscript: GeneViewTranscript;

  brush;
  zoomHistory: GeneViewZoomHistory;
  doubleClickTimer;
  windowResizeTimer;
  geneTableStats = {
    geneSymbol: '',
    chromosome: '',
    totalFamilyVariants: 0,
    selectedFamilyVariants: 0,
    totalSummaryVariants: 0,
    selectedSummaryVariants: 0,
  };
  denovoAllelesSpacings = {};
  additionalZeroAxisHeight = 0;
  constructor(
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
  ) {
    super();
  }

  ngOnInit() {
    this.setSvgScale(window.innerWidth);

    this.datasetsService.getSelectedDataset().subscribe(dataset => {
      this.geneBrowserConfig = dataset.geneBrowser;
      this.frequencyDomainMin = this.geneBrowserConfig.domainMin;
      this.frequencyDomainMax = this.geneBrowserConfig.domainMax;
      this.selectedFrequencies = [0, this.frequencyDomainMax];
      this.yAxisLabel = this.geneBrowserConfig.frequencyName || this.geneBrowserConfig.frequencyColumn;

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

    });

    this.streamingFinished$.subscribe(() => {
      this.geneViewModel = new GeneViewModel(this.gene, this.svgWidth);
      this.geneViewTranscript = new GeneViewTranscript(this.gene.transcripts[0]);
      this.setDefaultScale();
      this.resetCheckboxes();

      this.summaryVariantsArray = this.variantsArray;
      this.filteredSummaryVariantsArray = this.variantsArray;

      this.setDenovoPlotHeight();
      this.drawGene();
      this.setDefaultScale();
      this.updateFamilyVariantsTable();
      this.drawPlot();

      this.geneTableStats.geneSymbol = this.gene.gene;
      this.geneTableStats.chromosome = this.gene.transcripts[0].chrom;
      this.geneTableStats.totalSummaryVariants = this.summaryVariantsArray.summaryVariants.length;
      this.geneTableStats.totalFamilyVariants = this.summaryVariantsArray.totalFamilyVariantsCount;

      this.loadingService.setLoadingStop();
    });

    this.zoomHistory = new GeneViewZoomHistory();
  }

  resetCheckboxes() {
    const panelCheckboxes = [];
    panelCheckboxes.push(
      this.denovoCheckbox,
      this.transmittedCheckbox,
      ...this.affectedStatusCheckboxes,
      ...this.effectTypeCheckboxes,
      ...this.variantTypeCheckboxes
    );
    panelCheckboxes.forEach(element => {
      element.nativeElement.checked = true;
    });

    this.selectedEffectTypes = ['lgds', 'missense', 'synonymous', 'cnv+', 'cnv-', 'other'];
    this.selectedVariantTypes = ['sub', 'ins', 'del', 'cnv+', 'cnv-'];
    this.selectedAffectedStatus = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
    this.showDenovo = true;
    this.showTransmitted = true;
  }

  getState(): Observable<object> {
    const state = {
      'affectedStatus': Array.from(this.selectedAffectedStatus),
      'selectedEffectTypes': Array.from(this.selectedEffectTypes),
      'selectedVariantTypes': Array.from(this.selectedVariantTypes),
      'zoomState': this.zoomHistory.currentState,
      'showDenovo': this.showDenovo,
      'showTransmitted': this.showTransmitted,
      'summaryVariantIds': this.filteredSummaryVariantsArray.summaryVariants.map(sv => sv.svuid),
    };
    if (state['zoomState']) {
      state['regions'] = this.geneViewModel.collapsedGeneViewTranscript.resolveRegionChromosomes(
        [this.x.domain()[0], this.x.domain()[this.x.domain().length - 1]]
      );
    }
    return this.validateAndGetState(state);
  }

  enableIntronCondensing() {
    this.condenseIntrons = true;
  }

  disableIntronCondensing() {
    this.condenseIntrons = false;
  }

  drawDenovoIcons() {
    this.svgElement = d3.select('#denovo')
      .attr('width', 120)
      .attr('height', 20);
    draw.surroundingRectangle(this.svgElement, 10, 7.5, '#000000', 'Denovo LGDs');
    draw.star(this.svgElement, 10, 7.5, '#000000', 'Denovo LGDs');
    draw.surroundingRectangle(this.svgElement, 30, 8, '#000000', 'Denovo Missense');
    draw.triangle(this.svgElement, 30, 8, '#000000', 'Denovo Missense');
    draw.surroundingRectangle(this.svgElement, 50, 8, '#000000', 'Denovo Synonymous');
    draw.circle(this.svgElement, 50, 8, '#000000', 'Denovo Synonymous');
    draw.surroundingRectangle(this.svgElement, 70, 8, '#000000', 'Denovo Other');
    draw.dot(this.svgElement, 70, 8, '#000000', 'Denovo Other');
    draw.surroundingRectangle(this.svgElement, 90, 8, '#000000', 'Denovo CNV+');
    draw.rect(this.svgElement, 82, 98, 5, 6, '#000000', 0.4, 'Denovo CNV+');
    draw.surroundingRectangle(this.svgElement, 110, 8, '#000000', 'Denovo CNV-');
    draw.rect(this.svgElement, 102, 118, 7.5, 1, '#000000', 0.4, 'Denovo CNV-');
  }

  drawTransmittedIcons() {
    this.svgElement = d3.select('#transmitted')
      .attr('width', 125)
      .attr('height', 20);
    draw.star(this.svgElement, 10, 7.5, '#000000', 'LGDs');
    draw.triangle(this.svgElement, 30, 8, '#000000', 'Missense');
    draw.circle(this.svgElement, 50, 8, '#000000', 'Synonymous');
    draw.dot(this.svgElement, 70, 8, '#000000', 'Other');
    draw.rect(this.svgElement, 82, 98, 5, 6, '#000000', 0.4, 'CNV+');
    draw.rect(this.svgElement, 107, 125, 7.5, 1, '#000000', 0.4, 'CNV-');
  }

  drawEffectTypesIcons() {
    const effectIcons = {
      '#LGDs': draw.star,
      '#Missense': draw.triangle,
      '#Synonymous': draw.circle,
      '#Other': draw.dot
    };
    for (const [effect, drawIcon] of Object.entries(effectIcons)) {
      this.svgElement = d3.select(effect)
        .attr('width', 20)
        .attr('height', 20);
        drawIcon(this.svgElement, 10, 8, '#000000', effect);
    }

    this.svgElement = d3.select('#CNV\\+')
    .attr('width', 20)
    .attr('height', 20);
    draw.rect(
      this.svgElement, 5, 20,
      5, 6, '#000000', 0.4, 'CNV+'
    );

    this.svgElement = d3.select('#CNV-')
    .attr('width', 20)
    .attr('height', 20);
    draw.rect(
      this.svgElement, 5, 20,
      7.5, 1, '#000000', 0.4, 'CNV-'
    );
  }

  setSvgScale(windowWidth: number) {
    this.fontSize = this.calculateTextFontSize(windowWidth);
    this.svgWidth = windowWidth - this.options.margin.left - this.options.margin.right;
  }

  redraw() {
    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
    }
  }

  redrawAndUpdateTable() {
    this.setDenovoPlotHeight();
    this.redraw();
    this.updateFamilyVariantsTable();
  }

  recalculateXRange(domainMin: number, domainMax: number): number[] {
    let newRange: number[];
    if (this.condenseIntrons) {
      newRange = this.geneViewModel.buildCondensedIntronsRange(domainMin, domainMax, this.svgWidth);
    } else {
      newRange = this.geneViewModel.buildNormalIntronsRange(domainMin, domainMax, this.svgWidth);
    }
    return newRange;
  }

  checkShowDenovo(checked: boolean) {
    this.showDenovo = checked;
    this.redrawAndUpdateTable();
  }

  checkShowTransmitted(checked: boolean) {
    this.showTransmitted = checked;
    this.redrawAndUpdateTable();
  }

  checkEffectType(effectType: string, checked: boolean) {
    effectType = effectType.toLowerCase();
    if (checked) {
      this.selectedEffectTypes.push(effectType);
    } else {
      this.selectedEffectTypes.splice(this.selectedEffectTypes.indexOf(effectType), 1);
    }
    this.redrawAndUpdateTable();
  }

  checkVariantType(variantType: string, checked: boolean) {
    variantType = variantType.toLowerCase();
    if (checked) {
      this.selectedVariantTypes.push(variantType);
    } else {
      this.selectedVariantTypes.splice(this.selectedVariantTypes.indexOf(variantType), 1);
    }
    this.redrawAndUpdateTable();
  }

  checkAffectedStatus(affectedStatus: string, checked: boolean) {
    if (checked) {
      this.selectedAffectedStatus.push(affectedStatus);
    } else {
      this.selectedAffectedStatus.splice(this.selectedAffectedStatus.indexOf(affectedStatus), 1);
    }
    this.redrawAndUpdateTable();
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

  isVariantEffectSelected(worst_effect: string): boolean {
    let result = false;
    worst_effect = worst_effect.toLowerCase();

    if (this.selectedEffectTypes.indexOf(worst_effect) !== -1) {
      result = true;
    }

    if (this.lgds.indexOf(worst_effect) !== -1) {
      if (this.selectedEffectTypes.indexOf('lgds') !== -1) {
        result = true;
      }
    } else if (
      worst_effect !== 'missense' && worst_effect !== 'synonymous' &&
      worst_effect !== 'cnv+' && worst_effect !== 'cnv-' &&
      this.selectedEffectTypes.indexOf('other') !== -1
    ) {
      result = true;
    }

    return result;
  }

  frequencyIsSelected(frequency: number) {
    return frequency >= this.selectedFrequencies[0] && frequency <= this.selectedFrequencies[1];
  }

  toggleCondenseIntron() {
    const domainMin = this.x.domain()[0];
    const domainMax = this.x.domain()[this.x.domain().length - 1];
    this.condenseIntrons = !this.condenseIntrons;
    const domain = this.geneViewModel.buildDomain(domainMin, domainMax);
    this.x.domain(domain).range(this.recalculateXRange(domainMin, domainMax));
    this.zoomHistory.addStateToHistory(
      new GeneViewScaleState(domain, this.selectedFrequencies[0], this.selectedFrequencies[1], this.condenseIntrons)
    );
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

  getVariantAffectedStatus(summaryVariant: GeneViewSummaryAllele): string {
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

  isVariantTypeSelected(variantType: string): boolean {
    if (variantType.substr(0, 3) === 'cnv') {
      variantType = variantType.substr(0, 4);
    } else {
      variantType = variantType.substr(0, 3);
    }

    return this.selectedVariantTypes.includes(variantType) ? true : false;
  }

  filterSummaryVariant(summaryVariant: GeneViewSummaryVariant, startPos: number, endPos: number) {
    const result = new GeneViewSummaryVariant(summaryVariant.svuid);
    for (const summaryAllele of summaryVariant.summaryAlleles) {
      if (
        (!this.isVariantEffectSelected(summaryAllele.effect)) ||
        (!this.showDenovo && summaryAllele.seenAsDenovo) ||
        (!this.showTransmitted && !summaryAllele.seenAsDenovo) ||
        (!this.isAffectedStatusSelected(this.getVariantAffectedStatus(summaryAllele))) ||
        (!this.isVariantTypeSelected(summaryAllele.variant))
      ) {
        continue;
      } else if (this.frequencyIsSelected(summaryAllele.frequency)) {
        if (summaryAllele.isCNV()) {
          if (
            !(summaryAllele.position <= startPos && summaryAllele.endPosition <= startPos) &&
            !(summaryAllele.position >= endPos && summaryAllele.endPosition >= endPos)
          ) {
            result.push(summaryAllele);
          }
        } else  {
          if (summaryAllele.position >= startPos && summaryAllele.position <= endPos) {
            result.push(summaryAllele);
          }
        }
      }
    }
    return result;
  }

  filterSummaryVariantsArray(
    summaryVariantsArray: GeneViewSummaryVariantsArray, startPos: number, endPos: number
  ): GeneViewSummaryVariantsArray {
    const result = new GeneViewSummaryVariantsArray();
    for (const summaryVariant of summaryVariantsArray.summaryVariants) {
      result.push(this.filterSummaryVariant(summaryVariant, startPos, endPos));
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

  doAllelesIntersect(allele1: GeneViewSummaryAllele, allele2: GeneViewSummaryAllele): boolean {
    let result: boolean;

    if (!allele1.isCNV()) {
      allele1.endPosition = allele1.position;
    }

    if (!allele2.isCNV()) {
      allele2.endPosition = allele2.position;
    }

    if (this.x(allele1.endPosition) + 6 < this.x(allele2.position) - 6 ||
        this.x(allele1.position) - 6 > this.x(allele2.endPosition) + 6) {
      result = false;
    } else {
      result = true;
    }

    return result;
  }

  drawPlot() {
    const minDomain = this.x.domain()[0];
    const maxDomain = this.x.domain()[this.x.domain().length - 1];

    const filteredSummaryVariants = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, minDomain, maxDomain
    );
    this.filteredSummaryVariantsArray = filteredSummaryVariants;

    this.geneTableStats.selectedSummaryVariants = filteredSummaryVariants.summaryVariants.length;
    this.geneTableStats.selectedFamilyVariants = filteredSummaryVariants.totalFamilyVariantsCount;

    if (this.gene !== undefined) {
      this.x_axis = d3.axisBottom(this.x).tickValues(this.calculateXAxisTicks());
      this.y_axis = d3.axisLeft(this.y).tickValues(this.calculateYAxisTicks()).tickFormat(d3.format('1'));
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([]);
      this.y_axis_zero = d3.axisLeft(this.y_zero).tickSizeInner(0).tickPadding(9);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeightFreq})`).call(this.x_axis).style('font', `${this.fontSize}px sans-serif`);
      this.svgElement.append('g').call(this.y_axis).style('font', `${this.fontSize}px sans-serif`);
      this.svgElement.append('g').call(this.y_axis_subdomain).style('font', `${this.fontSize}px sans-serif`);
      this.svgElement.append('g').call(this.y_axis_zero).style('font', `${this.fontSize}px sans-serif`);


      this.svgElement.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - (this.options.margin.left - 45))
      .attr('x', 0 - (this.svgHeightFreq / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text(this.yAxisLabel);

      this.svgElement
        .append('svg')
        .append('g')
        .append('rect')
        .attr('height', this.svgHeightFreq - this.zeroAxisY)
        .attr('width', this.svgWidth)
        .attr('x', 0)
        .attr('y', this.zeroAxisY)
        .attr('fill', '#FFAD18')
        .attr('fill-opacity', '0.05');

      this.brush = d3.brush().extent([[0, 0], [this.svgWidth, this.svgHeightFreq]])
        .on('end', this.brushEndEvent);

      this.svgElement.append('g')
        .attr('class', 'brush')
        .call(this.brush);

      for (const variant of filteredSummaryVariants.summaryVariants) {
        for (const allele of variant.summaryAlleles) {
          const allelePosition = this.x(allele.position);
          const color = this.getAffectedStatusColor(this.getVariantAffectedStatus(allele));
          const alleleTitle = `Effect type: ${allele.effect}\nVariant position: ${allele.location}`;

          const alleleHeight = this.getVariantY(allele.frequency);

          let spacing = 0;
          if (allele.seenAsDenovo) {
            if (allele.frequency === null) {
              spacing = this.denovoAllelesSpacings[allele.svuid] + 8;
            }

            if (allele.isCNV()) {
              const cnvLength = this.x(allele.endPosition) - allelePosition;
              draw.surroundingRectangle(
                this.svgElement, allelePosition + cnvLength / 2,
                alleleHeight + spacing, color, alleleTitle, 1, cnvLength
              );
            } else {
              draw.surroundingRectangle(this.svgElement, allelePosition, alleleHeight + spacing, color, alleleTitle);
            }
          }

          if (allele.isLGDs()) {
            draw.star(this.svgElement, allelePosition, alleleHeight + spacing, color, alleleTitle);
          } else if (allele.isMissense()) {
            draw.triangle(this.svgElement, allelePosition, alleleHeight + spacing, color, alleleTitle);
          } else if (allele.isSynonymous()) {
            draw.circle(this.svgElement, allelePosition, alleleHeight + spacing, color, alleleTitle);
          } else if (allele.isCNVPlus()) {
            draw.rect(
              this.svgElement, this.x(allele.position), this.x(allele.endPosition),
              alleleHeight - 3 + spacing, 6, color, 1, alleleTitle
            );
          } else if (allele.isCNVPMinus()) {
            draw.rect(
              this.svgElement, this.x(allele.position), this.x(allele.endPosition),
              alleleHeight - 0.5 + spacing, 1, color, 1, alleleTitle
            );
          } else {
            draw.dot(this.svgElement, allelePosition, alleleHeight + spacing, color, alleleTitle);
          }
        }
      }
    }
  }

  calculateDenovoAllelesSpacings(summaryVariantsArray: GeneViewSummaryVariantsArray) {
    let denovoAlleles = [];
    for (const variant of summaryVariantsArray.summaryVariants) {
      for (const allele of variant.summaryAlleles) {
        if (allele.frequency === 0 && allele.seenAsDenovo) {
          allele.frequency = null;
          denovoAlleles.push(allele);
        }
      }
    }
    denovoAlleles.sort((sa, sa2) => sa.position > sa2.position ? 1 : sa.position < sa2.position ? -1 : 0)
    console.log(denovoAlleles);

    if (!denovoAlleles.length) {
      return;
    }

    const leveledDenovos: GeneViewSummaryAllele[][] = [];
    const denovoCount = denovoAlleles.length;
    for (let level = 0; level < denovoCount; level++) {
      leveledDenovos[level] = [];

      const toRemove = [];
      for (let i = 0; i < denovoAlleles.length; i++) {
        let canFitInLevel = true;

        for (let k = 0; k < leveledDenovos[level].length; k++) {
          if (this.doAllelesIntersect(leveledDenovos[level][k], denovoAlleles[i])) {
            canFitInLevel = false;
            break;
          }
        }

        if (canFitInLevel) {
          leveledDenovos[level].push(denovoAlleles[i]);
          toRemove.push(i);
        }
      }
      toRemove.reverse().forEach(index => {
        denovoAlleles.splice(index, 1);
      });

      if (denovoAlleles.length === 0) {
        break;
      }
    }

    const denovoAllelesSpacings = {};
    for (let row = 0; row < leveledDenovos.length; row++) {
      for (let col = 0; col < leveledDenovos[row].length; col++) {
        denovoAllelesSpacings[leveledDenovos[row][col].svuid] = 22 * row;
      }
    }

    return denovoAllelesSpacings;
  }

  setDenovoPlotHeight() {
    const minDomain = this.x.domain()[0];
    const maxDomain = this.x.domain()[this.x.domain().length - 1];
    const filteredSummaryVariants = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, minDomain, maxDomain
    );
    this.svgHeightFreqRaw = 400;
    this.svgHeightFreq = this.svgHeightFreqRaw - this.options.margin.top - this.options.margin.bottom;
    this.subdomainAxisY = Math.round(this.svgHeightFreq * this.options.axisScale.domain);
    this.zeroAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * this.options.axisScale.subdomain);

    this.denovoAllelesSpacings = this.calculateDenovoAllelesSpacings(filteredSummaryVariants);
    this.additionalZeroAxisHeight = 0;
    if (this.denovoAllelesSpacings) {
      this.additionalZeroAxisHeight = Math.max.apply(Math, Object.values(this.denovoAllelesSpacings));
    }

    this.svgHeightFreq += this.additionalZeroAxisHeight;
    this.svgHeightFreqRaw += this.additionalZeroAxisHeight;
    this.y_zero = d3.scalePoint()
    .domain(['0'])
    .range([this.svgHeightFreq, this.zeroAxisY]);
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
    const defaultScale = new GeneViewScaleState(domain, 0, this.frequencyDomainMax, this.condenseIntrons);
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

  clearSvgElement() {
    this.svgElement.selectAll('*').remove();
  }

  drawGene() {
    if (this.additionalZeroAxisHeight !== undefined) {
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

      let transcriptY = this.svgHeightFreqRaw + 30;
      this.drawTranscript(this.summedTranscriptElement, transcriptY, this.geneViewModel.collapsedGeneViewTranscript);
      transcriptY += 25;
      for (const geneViewTranscript of this.geneViewModel.geneViewTranscripts) {
        transcriptY += 25;
        this.drawTranscript(this.transcriptsElement, transcriptY, geneViewTranscript);
      }
    }
  }

  brushEndEvent = () => {
    this.updateBrush(d3.event.selection);
  }

  updateBrush(selection) {
    const extent = selection;

    const currentDomainMin = this.x.domain()[0];
    const currentDomainMax = this.x.domain()[this.x.domain().length - 1];

    if (!extent) {
      if (!this.doubleClickTimer) {
        this.doubleClickTimer = setTimeout(this.resetDoubleClickTimer, 250);
        return;
      }
      this.setDefaultScale();
    } else {
      if (currentDomainMax - currentDomainMin > 12) {
        const x1 = extent[0][0];
        const x2 = extent[1][0];
        const domainMin = Math.round(this.x.invert(Math.min(x1, x2)));
        const domainMax = Math.round(this.x.invert(Math.max(x1, x2)));
        this.updateXDomain(domainMin, domainMax);
      }

      const newFreqLimits = [
        this.convertBrushPointToFrequency(extent[0][1]),
        this.convertBrushPointToFrequency(extent[1][1])
      ];
      this.selectedFrequencies = [
        Math.min(...newFreqLimits),
        Math.max(...newFreqLimits),
      ];
      this.zoomHistory.addStateToHistory(
        new GeneViewScaleState(this.x.domain(), this.selectedFrequencies[0], this.selectedFrequencies[1], this.condenseIntrons)
      );
      this.svgElement.select('.brush').call(this.brush.move, null);
    }
    this.redrawAndUpdateTable();
  }

  updateXDomain(domainMin: number, domainMax: number) {
    if (domainMax - domainMin < 12) {
      const center = domainMin + Math.round((domainMax - domainMin) / 2);
      domainMin = center - 6;
      domainMax = center + 6;
    }

    this.x = d3.scaleLinear()
      .domain(this.geneViewModel.buildDomain(domainMin, domainMax))
      .range(this.recalculateXRange(domainMin, domainMax))
      .clamp(true);
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

  handleWindowResizeEvent($event) {
    if (!this.windowResizeTimer) {
      this.windowResizeTimer = setTimeout(this.resetWindowResizeTimer, 250);
      return;
    }

    if (this.gene !== undefined) {
      const windowWidth = $event.currentTarget.innerWidth;
      const domainMin = this.x.domain()[0];
      const domainMax = this.x.domain()[this.x.domain().length - 1];
      this.setSvgScale(windowWidth);
      this.geneViewModel.calculateRanges(this.svgWidth);
      this.x.range(this.recalculateXRange(domainMin, domainMax));
      this.redraw();
    }
  }

  drawFromHistory(scale: GeneViewScaleState) {
    this.x.domain(scale.xDomain);
    const domainMin = this.x.domain()[0];
    const domainMax = this.x.domain()[this.x.domain().length - 1];
    this.x.range(this.recalculateXRange(domainMin, domainMax));
    this.selectedFrequencies = [scale.yMin, scale.yMax];
    this.condenseIntrons = scale.condenseToggled;
    this.redrawAndUpdateTable();
  }

  resetDoubleClickTimer = () => {
    this.doubleClickTimer = null;
  }

  resetWindowResizeTimer = () => {
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
      draw.hoverText(
        element, (this.x(from) + this.x(to)) / 2 + 50, yPos + 35, `Chromosome: ${chromosome}`, `Chromosome: ${chromosome}`, this.fontSize
      );
    }
  }

  calculateXAxisTicks() {
    const ticks = [];
    const axisLength = this.x.range()[this.x.range().length - 1] - this.x.range()[0];
    const increment = Math.round(axisLength / (this.options.xAxisTicks - 1));
    for (let i = 0; i < axisLength; i += increment) {
      ticks.push(Math.round(this.x.invert(i)));
    }
    return ticks;
  }

  calculateYAxisTicks() {
    const ticks = [];
    for (let i = this.frequencyDomainMin; i <= this.frequencyDomainMax; i *= 10) {
      ticks.push(i);
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
    }
    this.drawTranscriptUTRText(element, firstSegmentStart, lastSegmentStop, yPos, geneViewTranscript.strand);

    let exonsLength = 0;
    for (const segment of segments) {
      const start = Math.max(domainMin, segment.start);
      const stop = Math.min(domainMax, segment.stop);
      const xStart = this.x(start);
      const xStop = this.x(stop);

      if (segment.isExon) {
        this.drawExon(element, xStart, xStop, yPos, segment.label, segment.isCDS, brushSize);
        exonsLength += segment.stop - segment.start;
      } else if (!segment.isSpacer) {
        this.drawIntron(element, xStart, xStop, yPos, segment.label, brushSize);
      }
    }

    if (transcriptId !== 'collapsed') {
      const formattedExonsLength = this.formatExonsLength(exonsLength);
      draw.hoverText(
        element,
        this.x(firstSegmentStart) - 50, yPos + 10,
        formattedExonsLength,
        `Transcript id: ${transcriptId}\nExons length: ${this.commaSeparateNumber(exonsLength)}`,
        this.fontSize
      );
    }
  }

  drawExon(element, xStart: number, xEnd: number, y: number, title: string, cds: boolean, brushSize) {
    let rectThickness = brushSize.nonCoding;
    if (cds) {
      rectThickness = brushSize.coding;
      y -= (brushSize.coding - brushSize.nonCoding) / 2;
      title += ' [CDS]';
    }
    draw.rect(element, xStart, xEnd, y, rectThickness, 'black', 1, title);
  }

  drawIntron(element, xStart: number, xEnd: number, y: number, title: string, brushSize) {
    draw.line(element, xStart, xEnd, y + brushSize.nonCoding / 2, title);
  }

  drawTranscriptUTRText(element, xStart: number, xEnd: number, y: number, strand: string) {
    const UTR = { left: '5\'', right: '3\'' };
    if (strand === '-') {
      UTR.left = '3\'';
      UTR.right = '5\'';
    }
    draw.hoverText(element, this.x(xStart) - 10, y + 10, UTR.left, `UTR ${UTR.left}`, this.fontSize);
    draw.hoverText(element, this.x(xEnd) + 20, y + 10, UTR.right, `UTR ${UTR.left}`, this.fontSize);
  }

  commaSeparateNumber(number: number): string {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  formatExonsLength(exonsLength: number): string {
    let result: string;
    const numLen = exonsLength.toString().length;

    if (numLen < 4) {
     result = `${exonsLength} bp`;
    } else if (numLen < 7) {
      result = `${Math.round(exonsLength / 100 + Number.EPSILON) / 10} kbp`;
    } else if (numLen < 10) {
      result = `${Math.round(exonsLength / 10000 + Number.EPSILON) / 10} mbp`;
    }

    return result;
  }
}
