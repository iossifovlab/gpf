import { Component, OnInit, Input, OnChanges, Output, EventEmitter } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Subject, Observable } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Transcript, Exon } from 'app/gene-view/gene';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';

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

  margin = {top: 10, right: 70, left: 70, bottom: 0};
  y_axes_proportions = {domain: 0.70, subdomain: 0.20, denovo: 0.10};
  svgElement;
  svgWidth = 1200 - this.margin.left - this.margin.right;
  svgHeight;
  svgHeightFreqRaw = 400;
  svgHeightFreq = this.svgHeightFreqRaw - this.margin.top - this.margin.bottom;

  subdomainAxisY = Math.round(this.svgHeightFreq * 0.75);
  denovoAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * 0.20);

  lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  x;
  y;
  y_subdomain;
  y_denovo;
  x_axis;
  y_axis;
  y_axis_subdomain;
  y_axis_denovo;
  variantsDataRepr = [];
  selectedEffectTypes = ['lgds', 'missense', 'synonymous', 'other'];

  selectedFrequencies;

  // GENE VIEW VARS
  brush;
  doubleClickTimer;

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
      this.selectedFrequencies = [-1, this.frequencyDomainMax]; // -1 signifies denovo variants

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
      .range([this.denovoAxisY, this.subdomainAxisY]);

      this.y_denovo = d3.scalePoint()
      .domain(['Denovo'])
      .range([this.svgHeightFreq, this.denovoAxisY]);
    });
    this.streamingFinished$.subscribe(() => {
      this.variantsArray = this.filterUnusableTransmittedVariants(this.variantsArray);
      this.drawPlot();
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
      if (genotypePreview.data.get('variant.is denovo') || frequency !== '-') {
        filteredVariants.push(genotypePreview);
      }
    }
    result.setGenotypePreviews(filteredVariants);
    return result;
  }

  filterTablePreviewVariantsArray(
    variantsArray: GenotypePreviewVariantsArray, startPos: number, endPos: number
  ): [GenotypePreviewVariantsArray, number[]] {
    const filteredVariants = [];
    const filteredVariantsPlot = [];
    const result = new GenotypePreviewVariantsArray();

    let location: string;
    let position: number;
    let frequency: string;
    for (const genotypePreview of variantsArray.genotypePreviews) {
      location = genotypePreview.data.get(this.locationColumn);
      position = Number(location.slice(location.indexOf(':') + 1));
      frequency = genotypePreview.data.get(this.frequencyColumn);
      if (!this.isVariantEffectSelected(genotypePreview.data.get(this.effectColumn))) {
        continue;
      } else if (position >= startPos && position <= endPos) {
        if (genotypePreview.data.get('variant.is denovo') && this.selectedFrequencies[0] === -1) {
          filteredVariants.push(genotypePreview);
          filteredVariantsPlot.push([position, -1, this.getVariantColor(genotypePreview.data.get(this.effectColumn))]);
        } else if (this.frequencyIsSelected(Number(frequency))) {
          filteredVariants.push(genotypePreview);
          filteredVariantsPlot.push([position, frequency, this.getVariantColor(genotypePreview.data.get(this.effectColumn))]);
        }
      }
    }
    result.setGenotypePreviews(filteredVariants);
    return [result, filteredVariantsPlot];
  }

  drawPlot() {
    const [filteredVariants, plotVariants] = this.filterTablePreviewVariantsArray(
      this.variantsArray, this.x.domain()[0], this.x.domain()[1]
    );

    console.log(this.countSummaryVariants(this.variantsArray));
    console.log(this.countSummaryVariants(filteredVariants));

    this.updateShownTablePreviewVariantsArrayEvent.emit(filteredVariants);
    if (this.gene !== undefined) {
      this.x_axis = d3.axisBottom(this.x).ticks(12);
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([0, this.frequencyDomainMin / 2.0]);
      this.y_axis_denovo = d3.axisLeft(this.y_denovo);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeightFreq})`).call(this.x_axis);
      this.svgElement.append('g').call(this.y_axis);
      this.svgElement.append('g').call(this.y_axis_subdomain);
      this.svgElement.append('g').call(this.y_axis_denovo);


      this.svgElement.append('rect')
      .attr('x', 0)
      .attr('y', this.denovoAxisY)
      .attr('width', this.svgWidth)
      .attr('height', this.svgHeightFreq - this.denovoAxisY)
      .style('fill', '#1E90FF')
      .style('opacity', 0.3);


      this.svgElement.append('g')
      .selectAll('dot')
      .data(plotVariants)
      .enter()
      .append('circle')
      .attr('cx', d => this.x(d[0]) )
      .attr('cy', d => {
        if (d[1] !== -1) {
          return d[1] < this.frequencyDomainMin ? this.y_subdomain(d[1]) : this.y(d[1]);
        } else {
          return this.y_denovo('Denovo');
        }
      } )
      .attr('r', 5)
      .style('fill', d => d[2])
      .style('opacity', 0.5);
    }
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
    this.selectedFrequencies = [-1, this.frequencyDomainMax];
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
    } else if (brushY < this.y_denovo.range()[1]) {
      return this.y_subdomain.invert(brushY);
    } else {
      return -1; // denovo
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
