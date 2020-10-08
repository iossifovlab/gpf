import { Component, OnInit, Input, OnChanges, Output, EventEmitter } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray, GenotypePreview } from 'app/genotype-preview-model/genotype-preview';
import { Subject, Observable } from 'rxjs';
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

  static fromPreivewVariant(genotypePreview: GenotypePreview): GeneViewSummaryVariant {
    const result = new GeneViewSummaryVariant(); 

    const location = genotypePreview.get("variant.location");
    result.location = location;
    result.position = Number(location.slice(location.indexOf(':') + 1));
    result.chrom = location.slice(0, location.indexOf(':'))

    let frequency: string = genotypePreview.data.get("freq.genome gnomad");
    if (frequency === '-') {
      frequency = '0.0';
    }
    result.frequency = Number(frequency);

    result.effect = genotypePreview.get("effect.worst effect type").toLowerCase();
    result.variant = genotypePreview.get("variant.variant");

    result.numberOfFamilyVariants = 1;

    result.seenAsDenovo = false;
    if (genotypePreview.get('variant.is denovo')) {
      result.seenAsDenovo = true;
    }
    result.seenInAffected = false;
    result.seenInUnaffected = false;

    result.svuid = result.location + ':' + result.variant;

    return result;
  }


}


class GeneViewSummaryVariantsArray {
  summaryVariants: GeneViewSummaryVariant[] = [];

  constructor(summaryVariants: IterableIterator<GeneViewSummaryVariant>) {
    for(const summaryVariant of summaryVariants) {
      this.summaryVariants.push(summaryVariant);
    }
  }

  static fromPreviewVariantsArray(previewVariants: GenotypePreviewVariantsArray): GeneViewSummaryVariantsArray {
    let summaryVariants: Map<string, GeneViewSummaryVariant> = new Map();

    for (const genotypePreview of previewVariants.genotypePreviews) {
      let summaryVariant = GeneViewSummaryVariant.fromPreivewVariant(genotypePreview);
      const svuid = summaryVariant.svuid;

      if(!summaryVariants.has(svuid)) {
        summaryVariants.set(svuid, summaryVariant);
      } else {
        let mergeSummaryVariant = summaryVariants.get(svuid);
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

  frequencyColumn: string;
  locationColumn: string;
  effectColumn: string;
  frequencyDomainMin: number;
  frequencyDomainMax: number;
  summaryVariantsArray: GeneViewSummaryVariantsArray;

  margin = {top: 10, right: 70, left: 70, bottom: 0};
  y_axes_proportions = {domain: 0.70, subdomain: 0.20};
  svgElement;
  svgWidth = 1200 - this.margin.left - this.margin.right;
  svgHeight;
  svgHeightFreqRaw = 400;
  svgHeightFreq = this.svgHeightFreqRaw - this.margin.top - this.margin.bottom;

  subdomainAxisY = Math.round(this.svgHeightFreq * 0.75);
  zeroAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * 0.2);

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

  // GENE VIEW VARS
  brush;
  doubleClickTimer;
  geneTableValues = {
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
      this.frequencyColumn = dataset.geneBrowser.frequencyColumn;
      this.locationColumn = dataset.geneBrowser.locationColumn;
      this.effectColumn = dataset.geneBrowser.effectColumn;
      this.frequencyDomainMin = dataset.geneBrowser.domainMin;
      this.frequencyDomainMax = dataset.geneBrowser.domainMax;
      this.selectedFrequencies = [0, this.frequencyDomainMax];

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
      this.variantsArray = this.filterUnusableTransmittedVariants(this.variantsArray);
      this.summaryVariantsArray = GeneViewSummaryVariantsArray.fromPreviewVariantsArray(this.variantsArray);

      this.drawPlot();

      this.geneTableValues.geneSymbol = this.gene.gene;
      this.geneTableValues.chromosome = this.gene.transcripts[0].chrom;
      this.geneTableValues.totalFamilyVariants = this.variantsArray.genotypePreviews.length;
      this.geneTableValues.totalSummaryVariants = this.countSummaryVariants(this.variantsArray);

      this.loadingService.setLoadingStop();
    });
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.setDefaultScale();
      this.drawGene();
    }
  }

  checkEffectType(effectType, checked) {
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

  extractPosition(location) {
    const idx = location.indexOf(':');
    return location.slice(idx + 1);
  }

  getVariantColor(worst_effect) {
    worst_effect = worst_effect.toLowerCase();

    if (this.lgds.indexOf(worst_effect) !== -1 || worst_effect === 'lgds') {
      return '#ff0000';
    } else if ( worst_effect === 'missense') {
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

  countSummaryVariants(variantsArray: GenotypePreviewVariantsArray) {
    const summaryVariants: Set<string> = new Set();
    for (const genotypePreview of variantsArray.genotypePreviews) {
      summaryVariants.add(
        genotypePreview.data.get(this.locationColumn)
        + genotypePreview.data.get('variant.variant')
      );
    }
    return summaryVariants.size;
  }

  filterUnusableTransmittedVariants(variantsArray: GenotypePreviewVariantsArray) {
    // Filter out transmitted variants without any frequency value, i.e. "-"
    const filteredVariants = [];
    const result = new GenotypePreviewVariantsArray();

    let frequency: string;
    for (const genotypePreview of variantsArray.genotypePreviews) {
      frequency = genotypePreview.data.get(this.frequencyColumn);
      filteredVariants.push(genotypePreview);
    }
    result.setGenotypePreviews(filteredVariants);
    return result;
  }

  filterTablePreviewVariantsArray(
    variantsArray: GenotypePreviewVariantsArray, startPos: number, endPos: number
  ): [GenotypePreviewVariantsArray, number[], number[]] {
    const filteredVariants = [];
    const filteredVariantsPlot = [];
    const filteredVariantsPlotDenovo = [];
    const result = new GenotypePreviewVariantsArray();

    let location: string;
    let position: number;
    let frequency: string;
    for (const genotypePreview of variantsArray.genotypePreviews) {
      location = genotypePreview.data.get(this.locationColumn);
      position = Number(location.slice(location.indexOf(':') + 1));
      frequency = genotypePreview.data.get(this.frequencyColumn);
      if (frequency === '-') {
        frequency = '0.0';
      }
      if (!this.isVariantEffectSelected(genotypePreview.data.get(this.effectColumn))) {
        continue;
      } else if (position >= startPos && position <= endPos) {
        if (this.frequencyIsSelected(Number(frequency))) {
          filteredVariants.push(genotypePreview);
          const plotVariant = [position, Number(frequency), this.getVariantColor(genotypePreview.data.get(this.effectColumn))];
          if (genotypePreview.data.get('variant.is denovo')) {
            filteredVariantsPlotDenovo.push(plotVariant);
          } else {
            filteredVariantsPlot.push(plotVariant);
          }
        }
      }
    }
    result.setGenotypePreviews(filteredVariants);
    return [result, filteredVariantsPlot, filteredVariantsPlotDenovo];
  }

  drawPlot() {
    const [filteredVariants, transmittedPlotVariants, denovoPlotVariants] = this.filterTablePreviewVariantsArray(
      this.variantsArray, this.x.domain()[0], this.x.domain()[1]
    );

    this.geneTableValues.selectedFamilyVariants = filteredVariants.genotypePreviews.length;
    this.geneTableValues.selectedSummaryVariants = this.countSummaryVariants(filteredVariants);

    this.updateShownTablePreviewVariantsArrayEvent.emit(filteredVariants);
    if (this.gene !== undefined) {
      this.x_axis = d3.axisBottom(this.x).ticks(12);
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([this.frequencyDomainMin / 2.0]);
      this.y_axis_zero = d3.axisLeft(this.y_zero);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeightFreq})`).call(this.x_axis);
      this.svgElement.append('g').call(this.y_axis);
      this.svgElement.append('g').call(this.y_axis_subdomain);
      this.svgElement.append('g').call(this.y_axis_zero);

      for (const variant of transmittedPlotVariants) {
        this.drawTransmittedPlotVariant(variant);
      }

      for (const variant of denovoPlotVariants) {
        this.drawDenovoPlotVariant(variant);
      }
    }
  }

  drawTransmittedPlotVariant(variantInfo) {
    this.svgElement.append('g')
    .append('circle')
    .attr('cx', this.x(variantInfo[0]))
    .attr(
      'cy', variantInfo[1] === 0 ?
      this.y_zero('0') :
      variantInfo[1] < this.frequencyDomainMin ?
      this.y_subdomain(variantInfo[1]) :
      this.y(variantInfo[1])
    )
    .attr('r', 5)
    .style('fill', variantInfo[2])
    .style('opacity', 0.5);
  }

  drawDenovoPlotVariant(variantInfo) {
    this.svgElement.append('g')
    .select('dot')
    .append('polygon')
    .attr('points', variantInfo => this.getTrianglePoints(
      this.x(variantInfo[0]),
      variantInfo[1] === 0 ?
      this.y_zero('0') :
      variantInfo[1] < this.frequencyDomainMin ?
      this.y_subdomain(variantInfo[1]) :
      this.y(variantInfo[1]),
      15
    ))
    .style('stroke-width', 2)
    .style('stroke', '#000000')
    .style('fill', variantInfo[2])
    .style('opacity', 0.5);
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
    this.selectedFrequencies = [0, this.frequencyDomainMax];
  }

  resetGeneTableValues(): void {
    this.geneTableValues = {
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

    let transcriptYPosition = this.svgHeightFreqRaw + 20;
    for (let i = 0; i < this.gene.transcripts.length; i++) {
      this.drawTranscript(i, transcriptYPosition);
      transcriptYPosition += 50;
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
      if (this.x.domain()[1] - this.x.domain()[0] > 12) {
        const newXmin = Math.round(this.x.invert(extent[0][0]));
        let newXmax = Math.round(this.x.invert(extent[1][0]));
        if (newXmax - newXmin < 12) {
          newXmax = newXmin + 12;
        }
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

  getCDSTransitionPos(transcript: Transcript, exon: Exon) {
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

  isInCDS(transcript: Transcript, start: number, stop: number) {
    return (start >= transcript.cds[0]) && (stop <= transcript.cds[1]);
  }

  drawTranscript(transcriptId: number, yPos: number) {
    const transcript = this.gene.transcripts[transcriptId];
    const firstStart = transcript.exons[0].start;
    const strand = transcript.strand;
    const totalExonCount = transcript.exons.length;
    let lastEnd = null;
    let i = 1;
    for (const exon of transcript.exons) {

      const transitionPos = this.getCDSTransitionPos(transcript, exon);

      if (lastEnd) {
        this.drawIntron(lastEnd, exon.start, yPos, `intron ${i - 1}/${totalExonCount - 1}`);
      }

      if (transitionPos !== null) {
        this.drawExon(
          exon.start, transitionPos, yPos,
          `exon ${i}/${totalExonCount}`,
          this.isInCDS(transcript, exon.start, transitionPos)
        );
        this.drawExon(
          transitionPos, exon.stop, yPos,
          `exon ${i}/${totalExonCount}`,
          this.isInCDS(transcript, transitionPos, exon.stop)
        );
      } else {
        this.drawExon(
          exon.start, exon.stop, yPos,
          `exon ${i}/${totalExonCount}`,
          this.isInCDS(transcript, exon.start, exon.stop)
        );
      }

      lastEnd = exon.stop;
      i += 1;
    }

    this.drawTranscriptUTRText(firstStart, lastEnd, yPos, strand);
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
    const UTR = {left: '5\'', right: '3\''};

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
