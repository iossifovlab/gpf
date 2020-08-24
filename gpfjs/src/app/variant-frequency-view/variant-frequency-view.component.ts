import { Component, OnInit, Input, OnChanges } from '@angular/core';
import * as d3 from 'd3';
import { Gene } from 'app/gene-view/gene';
import { QueryService } from 'app/query/query.service';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Subject } from 'rxjs';
// import { Gene } from './gene';

@Component({
  selector: 'gpf-variant-frequency-view',
  templateUrl: './variant-frequency-view.component.html',
  styleUrls: ['./variant-frequency-view.component.css']
})
export class VariantFrequencyViewComponent implements OnInit, OnChanges {
  @Input() gene: Gene;
  @Input() variantsArray: GenotypePreviewVariantsArray;
  @Input() streamingFinished$: Subject<boolean>;

	margin = {top: 10, right: 30, left: 70, bottom: 60}
  y_axes_proportions = {domain: 0.75, subdomain: 0.20, denovo: 0.05}

  svgElement;
  svgWidth = 1200 - this.margin.left - this.margin.right;
  svgHeight = 400 - this.margin.top - this.margin.bottom;

  a = Math.round(this.svgHeight * 0.75);
  b = this.a + Math.round(this.svgHeight * 0.20);

  x;
  y;
  y_subdomain;
  y_denovo;
  x_axis;
  y_axis;
  y_axis_subdomain;
  y_axis_denovo;
	variantsDataRepr = [];

  constructor() { }

  ngOnInit() {
    this.svgElement = d3.select('#svg-container-asdf')
    .append('svg')
    .attr('width', this.svgWidth + this.margin.left + this.margin.right)
    .attr('height', this.svgHeight + this.margin.top + this.margin.bottom)
		.append('g')
		.attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);

    this.x = d3.scaleLinear()
    .domain([0, 0])
    .range([0, this.svgWidth])

    this.y = d3.scaleLog()
    .domain([0.1, 1])
    .range([this.a, 0]);

    this.y_subdomain = d3.scaleLinear()
    .domain([0, 0.1])
    .range([this.b, this.a]);

    this.y_denovo = d3.scalePoint()
    .domain(["Denovo"])
    .range([this.svgHeight, this.b]);

		this.streamingFinished$.subscribe(() => this.drawPlot());
  }

  ngOnChanges() { }

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
      this.variantsDataRepr.push(
        {
          position: this.extractPosition(v.get("variant.location")),
          frequency: v.get("freq.genome gnomad"),
          color: this.getVariantColor(v.get("effect.worst effect"))
        }
      )
		}
	}

	drawPlot() {
		this.hydrateVariantsData(this.variantsArray);

    if (this.gene !== undefined) {
      this.svgElement.selectAll('*').remove();
      this.setDefaultScale();
      this.x_axis = d3.axisBottom(this.x);
      this.y_axis = d3.axisLeft(this.y);
      this.y_axis_subdomain = d3.axisLeft(this.y_subdomain).tickValues([0, 0.05]);
      this.y_axis_denovo = d3.axisLeft(this.y_denovo);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeight})`).call(this.x_axis);
			this.svgElement.append('g').call(this.y_axis);
			this.svgElement.append('g').call(this.y_axis_subdomain);
			this.svgElement.append('g').call(this.y_axis_denovo);


      this.svgElement.append('rect')
      .attr("x", 0)
      .attr("y", this.b)
      .attr("width", this.svgWidth)
      .attr("height", this.svgHeight - this.b)
      .style("fill", "orange")
      .style("stroke", "black")
      .style("opacity", 0.3);


			this.svgElement.append('g')
			.selectAll("dot")
			.data(this.variantsDataRepr)
			.enter()
			.append("circle")
			.attr("cx", d => { return this.x(d.position)} )
			.attr("cy", d => { return d.frequency !== "-" ? d.frequency < 0.1 ? this.y_subdomain(d.frequency) : this.y(d.frequency) : this.y_denovo("Denovo")} )
			.attr("r", 5)
			.style("fill", d => { return d.color })
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
}
