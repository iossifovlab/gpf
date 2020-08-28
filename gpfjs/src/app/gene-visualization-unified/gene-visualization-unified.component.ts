import { Component, OnInit, Input, OnChanges } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { QueryService } from 'app/query/query.service';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Subject } from 'rxjs';
// import { Gene } from './gene';

@Component({
  selector: 'gpf-gene-visualization-unified',
  templateUrl: './gene-visualization-unified.component.html',
  styleUrls: ['./gene-visualization-unified.component.css']
})
export class GeneVisualizationUnifiedComponent implements OnInit {
  @Input() gene: Gene;
  @Input() variantsArray: GenotypePreviewVariantsArray;
  @Input() streamingFinished$: Subject<boolean>;

	margin = {top: 10, right: 30, left: 70, bottom: 0}
  y_axes_proportions = {domain: 0.70, subdomain: 0.20, denovo: 0.10}

  svgElement;
  svgWidth = 1200 - this.margin.left - this.margin.right;
  svgHeight;
  svgHeightFreqRaw = 400;
  svgHeightFreq = this.svgHeightFreqRaw - this.margin.top - this.margin.bottom;

  subdomainAxisY = Math.round(this.svgHeightFreq * 0.75);
  denovoAxisY = this.subdomainAxisY + Math.round(this.svgHeightFreq * 0.20);

  x;
  y;
  y_subdomain;
  y_denovo;
  x_axis;
  y_axis;
  y_axis_subdomain;
  y_axis_denovo;
	variantsDataRepr = [];

  // GENE VIEW VARS
  brush;
  doubleClickTimer;

  constructor() { }

  ngOnInit() {
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
    .domain([0.01, 100])
    .range([this.subdomainAxisY, 0]);

    this.y_subdomain = d3.scaleLinear()
    .domain([0, 0.01])
    .range([this.denovoAxisY, this.subdomainAxisY]);

    this.y_denovo = d3.scalePoint()
    .domain(["Denovo"])
    .range([this.svgHeightFreq, this.denovoAxisY]);

		this.streamingFinished$.subscribe(() => {this.drawPlot()});
  }

  ngOnChanges() {
    if (this.gene !== undefined) {
      this.setDefaultScale();
      this.drawGene();
    }
  }

	extractPosition(location) {
		let idx = location.indexOf(":")
		return location.slice(idx + 1);
	}

	getVariantColor(worst_effect) {
		worst_effect = worst_effect.toLowerCase();

		let lgds = ["nonsense", "splice-site", "frame-shift", "no-frame-shift-new-stop"]

		if(lgds.indexOf(worst_effect) !== -1) {
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

	hydrateVariantsData(variantsArray) {
		this.variantsDataRepr = [];
		for(let v of variantsArray.genotypePreviews) {
      if(v.get("freq.genome gnomad") !== "-" || v.get("variant.is denovo")) {
        this.variantsDataRepr.push(
          {
            position: this.extractPosition(v.get("variant.location")),
            frequency: v.get("freq.genome gnomad") === "-" ? "denovo" : v.get("freq.genome gnomad"),
            color: this.getVariantColor(v.get("effect.worst effect")),
          }
        )
      }
		}
	}

	drawPlot() {
		this.hydrateVariantsData(this.variantsArray);

    if (this.gene !== undefined) {
      // this.svgElement.selectAll('*').remove();
      // this.setDefaultScale();
      this.x_axis = d3.axisBottom(this.x).ticks(12);
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([0, 0.005]);
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
      .style("fill", "orange")
      .style("stroke", "black")
      .style("opacity", 0.3);


			this.svgElement.append('g')
			.selectAll("dot")
			.data(this.variantsDataRepr)
			.enter()
			.append("circle")
			.attr("cx", d => { return this.x(d.position)} )
			.attr("cy", d => { return d.frequency !== "denovo" ? d.frequency < 0.1 ? this.y_subdomain(d.frequency) : this.y(d.frequency) : this.y_denovo("Denovo")} )
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

    let transcriptYPosition = this.svgHeightFreqRaw + 20;
    for (let i = 0; i < this.gene.transcripts.length; i++) {
      this.drawTranscript(i, transcriptYPosition);
      transcriptYPosition += 50;
    }

    this.brush = d3.brushX().extent([[0, 0], [this.svgWidth, this.svgHeight]])
    .on('end', this.brushEndEvent);

    this.svgElement.append('g')
    .attr('class', 'brush')
    .call(this.brush);
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
    let lastEnd = null;
    const strand = this.gene.transcripts[transcriptId].strand;

    for (const exon of this.gene.transcripts[transcriptId].exons) {
      if (lastEnd) {
        this.drawIntron(lastEnd, exon.start, yPos, strand);
      }
      this.drawExon(exon.start, exon.stop, yPos);

      lastEnd = exon.stop;
    }
  }

  drawExon(xStart: number, xEnd: number, y: number) {
    this.drawRect(xStart, xEnd, y, 10, 'Exon ?/?');
  }

  drawIntron(xStart: number, xEnd: number, y: number, strand: string) {
    this.drawLine(xStart, xEnd, y + 4, 2, 'Intron ?/?', strand);
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

  drawLine(xStart: number, xEnd: number, y: number, height: number, svgTitle: string, strand: string) {
    let arrowX1Index;
    if (strand === '-') {
      arrowX1Index = 12.5;
    } else {
      arrowX1Index = 17.5;
    }

    let xStartAligned = this.x(xStart);
    let xEndAligned = this.x(xEnd);

    this.svgElement.append('line')
    .attr('x1', xStartAligned)
    .attr('y1', y + 1)
    .attr('x2', xEndAligned)
    .attr('y2', y + 1)
    .attr('stroke', 'black');

    // for (xStartAligned; xStartAligned < xEndAligned; xStartAligned += 50) {
    //   this.svgElement.append('line')
    //   .attr('x1', xStartAligned + arrowX1Index)
    //   .attr('y1', y + 3)
    //   .attr('x2', xStartAligned + 15)
    //   .attr('y2', y + 1)
    //   .attr('stroke', 'black')
    //   .attr('opacity', 0.7);

    //   this.svgElement.append('line')
    //   .attr('x1', xStartAligned + arrowX1Index)
    //   .attr('y1', y - 1)
    //   .attr('x2', xStartAligned + 15)
    //   .attr('y2', y + 1)
    //   .attr('opacity', 0.7)
    //   .attr('stroke', 'black');
    // }
  }
}
