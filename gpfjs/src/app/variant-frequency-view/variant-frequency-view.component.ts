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

	margin = {top: 10, right: 30, left: 30, bottom: 60}

  svgElement;
  svgWidth = 1000 - this.margin.left - this.margin.right;
  svgHeight = 400 - this.margin.top - this.margin.bottom;
  x;
  y;
  x_axis;
  y_axis;
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
    .domain([0.001, 1])
    .range([this.svgHeight, 0]);

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
			if(v.get("freq.genome gnomad") !== "-") {
				this.variantsDataRepr.push(
					{
						position: this.extractPosition(v.get("variant.location")),
						frequency: v.get("freq.genome gnomad"),
						color: this.getVariantColor(v.get("effect.worst effect"))
					}
				)
			}
		}
	}

	drawPlot() {
		this.hydrateVariantsData(this.variantsArray);

    if (this.gene !== undefined) {
      this.svgElement.selectAll('*').remove();
      this.setDefaultScale();
      this.x_axis = d3.axisBottom(this.x);
      this.y_axis = d3.axisLeft(this.y);
      this.svgElement.append('g').attr('transform', `translate(0, ${this.svgHeight})`).call(this.x_axis);
			this.svgElement.append('g').call(this.y_axis);

			this.svgElement.append('g')
			.selectAll("dot")
			.data(this.variantsDataRepr)
			.enter()
			.append("circle")
			.attr("cx", d => { return this.x(d.position)} )
			.attr("cy", d => { return this.y(d.frequency)} )
			.attr("r", 5)
			.style("fill", d => { return d.color })
    }
	}

  setDefaultScale(): void {
    const a = this.gene.transcripts[0].exons;
    const b = this.gene.transcripts[1].exons;

    const domainBeginning = Math.min(a[0].start, b[0].start);
    const domainEnding = Math.max(a[a.length - 1].stop, b[b.length - 1].stop);

    this.x.domain([domainBeginning, domainEnding]);
  }
}
