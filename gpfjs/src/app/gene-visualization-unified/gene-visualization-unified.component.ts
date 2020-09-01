import { Component, OnInit, Input, OnChanges } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Subject, Observable } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-gene-visualization-unified',
  templateUrl: './gene-visualization-unified.component.html',
  styleUrls: ['./gene-visualization-unified.component.css']
})
export class GeneVisualizationUnifiedComponent implements OnInit {
  @Input() gene: Gene;
  @Input() variantsArray: GenotypePreviewVariantsArray;
  @Input() streamingFinished$: Subject<boolean>;

  frequencyColumn;
  frequencyDomainMin: number;
  frequencyDomainMax: number;

	margin = {top: 10, right: 70, left: 70, bottom: 0}
  y_axes_proportions = {domain: 0.70, subdomain: 0.20, denovo: 0.10}
  svgElement;
  svgWidth = 1200 - this.margin.left - this.margin.right;
  svgHeight;
  svgHeightFreqRaw = 400;
  svgHeightFreq = this.svgHeightFreqRaw - this.margin.top - this.margin.bottom;

  subdomainAxisY = Math.round(this.svgHeightFreq * 0.75);
  denovoAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * 0.20);
	
	lgds = ["nonsense", "splice-site", "frame-shift", "no-frame-shift-new-stop"];

  x;
  y;
  y_subdomain;
  y_denovo;
  x_axis;
  y_axis;
  y_axis_subdomain;
  y_axis_denovo;
	variantsDataRepr = [];
	selectedEffectTypes = ["lgds", "missense", "synonymous", "other"];

  // GENE VIEW VARS
  brush;
  doubleClickTimer;
  
  constructor(
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit() {
    this.datasetsService.getSelectedDataset().subscribe(dataset => {
      this.frequencyColumn = dataset.geneBrowser.frequencyColumn;
      this.frequencyDomainMin = dataset.geneBrowser.domainMin;
      this.frequencyDomainMax = dataset.geneBrowser.domainMax;

      this.svgElement = d3.select('#svg-container')
      .append('svg')
      .attr('width', this.svgWidth + this.margin.left + this.margin.right)
      .attr('height', this.svgHeightFreqRaw)
      .append('g')
      .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);

      this.x = d3.scaleLinear()
      .domain([0, 0])
      .range([0, this.svgWidth])

      this.y = d3.scaleLog()
      .domain([this.frequencyDomainMin, this.frequencyDomainMax])
      .range([this.subdomainAxisY, 0]);

      this.y_subdomain = d3.scaleLinear()
      .domain([0, this.frequencyDomainMin])
      .range([this.denovoAxisY, this.subdomainAxisY]);

      this.y_denovo = d3.scalePoint()
      .domain(["Denovo"])
      .range([this.svgHeightFreq, this.denovoAxisY]);
    });
    this.streamingFinished$.subscribe(() => {this.drawPlot()});
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.setDefaultScale();
      this.drawGene();
    }
  }

	checkEffectType(effectType, checked) {
		effectType = effectType.toLowerCase();
		if(checked) this.selectedEffectTypes.push(effectType);
    else this.selectedEffectTypes.splice(this.selectedEffectTypes.indexOf(effectType), 1);
    
    if (this.gene !== undefined) {
      this.drawGene();
      this.drawPlot();
    }
	}

	extractPosition(location) {
		let idx = location.indexOf(":")
		return location.slice(idx + 1);
	}

	getVariantColor(worst_effect) {
    worst_effect = worst_effect.toLowerCase();

		if(this.lgds.indexOf(worst_effect) !== -1 || worst_effect == "lgds") {
			return "#ff0000";
		}
		else if(worst_effect == "missense") {
			return "#ffff00";
		}
		else if(worst_effect == "synonymous") {
			return "#69b3a2";
		}
		else {
			return "#555555";
		}
	}

	isVariantEffectSelected(worst_effect) {
		worst_effect = worst_effect.toLowerCase();

		if(this.selectedEffectTypes.indexOf(worst_effect) !== -1) {
			return true
		}

		if(this.lgds.indexOf(worst_effect) !== -1) {
			if(this.selectedEffectTypes.indexOf("lgds") !== -1) {
				return true;
			}
		}
		else if(worst_effect !== "missense" && worst_effect !== "synonymous" && this.selectedEffectTypes.indexOf("other") !== -1) {
			return true;
		}
		return false;
	}

	hydrateVariantsData(variantsArray) {
		this.variantsDataRepr = [];
		for(let v of variantsArray.genotypePreviews) {
			if(this.isVariantEffectSelected(v.get("effect.worst effect type"))) {
				if(v.get(this.frequencyColumn) !== "-" || v.get("variant.is denovo")) {
					this.variantsDataRepr.push(
						{
							position: this.extractPosition(v.get("variant.location")),
							frequency: v.get(this.frequencyColumn) === "-" ? "denovo" : v.get(this.frequencyColumn),
							color: this.getVariantColor(v.get("effect.worst effect type")),
						}
					)
				}
			}
		}
	}

	drawPlot() {
		this.hydrateVariantsData(this.variantsArray);

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
      .attr("x", 0)
      .attr("y", this.denovoAxisY)
      .attr("width", this.svgWidth)
      .attr("height", this.svgHeightFreq - this.denovoAxisY)
      .style("fill", "#1E90FF")
      .style("opacity", 0.3);


			this.svgElement.append('g')
			.selectAll("dot")
			.data(this.variantsDataRepr)
			.enter()
			.append("circle")
			.attr("cx", d => { return this.x(d.position)} )
			.attr("cy", d => { return d.frequency !== "denovo" ? d.frequency < this.frequencyDomainMin ? this.y_subdomain(d.frequency) : this.y(d.frequency) : this.y_denovo("Denovo")} )
			.attr("r", 5)
			.style("fill", d => { return d.color })
      .style("opacity", 0.5);
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

    this.brush = d3.brushX().extent([[0, 0], [this.svgWidth, this.svgHeight]])
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
      if(this.x.domain()[1] - this.x.domain()[0] > 12) {
        let newXmin = Math.round(this.x.invert(extent[0]));
        let newXmax = Math.round(this.x.invert(extent[1]));
        if(newXmax - newXmin < 12) {
          newXmax = newXmin + 12;
        }
        this.x.domain([newXmin, newXmax]);
      }
      this.svgElement.select('.brush').call(this.brush.move, null);
    }
    this.drawGene();
    this.drawPlot();
  }

  resetTimer = () => {
    this.doubleClickTimer = null;
  }

  drawTranscript(transcriptId: number, yPos: number) {
    const transcript = this.gene.transcripts[transcriptId];
    const firstStart = transcript.exons[0].start;
    const strand = transcript.strand;
    const totalExonCount = transcript.exons.length;

    let lastEnd = null;
    let i = 1;
    for (const exon of transcript.exons) {
      if (lastEnd) {
        this.drawIntron(lastEnd, exon.start, yPos, `intron ${i - 1}/${totalExonCount - 1}`);
      }
      this.drawExon(exon.start, exon.stop, yPos, `exon ${i}/${totalExonCount}`);

      lastEnd = exon.stop;
      i += 1;
    }

    this.drawTranscriptUTRText(firstStart, lastEnd, yPos, strand);
  }

  drawExon(xStart: number, xEnd: number, y: number, title: string) {
    this.drawRect(xStart, xEnd, y, 10, title);
  }

  drawIntron(xStart: number, xEnd: number, y: number, title: string) {
    this.drawLine(xStart, xEnd, y, title);
  }

  drawTranscriptUTRText(xStart: number, xEnd: number, y: number, strand: string) {
    let UTR = {left: '5\'', right: '3\''}

    if (strand === '-') {
      UTR.left = '3\'';
      UTR.right = '5\'';
    }

    this.svgElement.append("text")
    .attr("y", y + 10)
    .attr("x", this.x(xStart) - 20)
    .attr('font-size', '13px')
    .text(UTR.left)
    .attr('cursor', 'default')
    .append('svg:title').text(`UTR ${UTR.left}`)

    this.svgElement.append("text")
    .attr("y", y + 10)
    .attr("x", this.x(xEnd) + 10)
    .attr('font-size', '13px')
    .text(UTR.right)
    .attr('cursor', 'default')
    .append('svg:title').text(`UTR ${UTR.right}`)
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

  drawLine(xStart: number, xEnd: number, y: number, svgTitle: string) {
    let xStartAligned = this.x(xStart);
    let xEndAligned = this.x(xEnd);

    this.svgElement.append('line')
    .attr('x1', xStartAligned)
    .attr('y1', y + 5)
    .attr('x2', xEndAligned)
    .attr('y2', y + 5)
    .attr('stroke', 'black')
    .append('svg:title').text(svgTitle);
  }
}
