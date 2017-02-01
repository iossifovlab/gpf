import { Input, Component, OnInit, ViewChild } from '@angular/core';
import { GeneWeights } from './gene-weights';
import { GeneWeightsService } from './gene-weights.service';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-gene-weights',
  templateUrl: './gene-weights.component.html'
})
export class GeneWeightsComponent {
  @Input() width: number;
  @Input() height: number;
  @Input() marginLeft = 40;
  @Input() marginTop = 30;
  @ViewChild('histogramContainer') histogramContainer: any;
  geneWeights: GeneWeights[];

  constructor(private geneWeightsService: GeneWeightsService) {

  }


  redrawHistogram(geneWeights: GeneWeights) {


    let barsBinsArray = [];
    for (var i = 0; i < geneWeights.bars.length; i++) {
      barsBinsArray[i] = {
        bin: geneWeights.bins[i],
        bar: geneWeights.bars[i]
      };
    }

    let width = this.width - this.marginLeft * 2;
    let height = this.height - this.marginTop * 2 - 100;
    let barWidth = width / geneWeights.bars.length;
    let outerSvg = d3.select(this.histogramContainer.nativeElement)
      .append("svg")
      .attr("width", this.width)
      .attr("height", this.height)
      .append("g")
      .attr("transform", "translate(" + this.marginLeft + "," + this.marginTop + ")");
    let svg =   outerSvg.append("g")
      .attr("transform", "translate(0, 50)");

    var x = d3.scaleLinear()
      .domain([geneWeights.min, geneWeights.max])
      .rangeRound([0, width]);

    var y = d3.scaleLinear().range([height, 0]);

    y.domain([0, d3.max(geneWeights.bars)]);
    // Add the x Axis
    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x));

    let leftAxis = d3.axisLeft(y);
    leftAxis.ticks(5);
    svg.append("g")
        .call(leftAxis);

    svg.selectAll("bar")
      .data(barsBinsArray)
      .enter().append("rect")
      .style("fill", "steelblue")
      .attr("x", function(d: any) { return x(d.bin); })
      .attr("width", barWidth)
      .attr("y", function(d: any) { return y(d.bar); })
      .attr("height", function(d: any) { return height - y(d.bar); });

    function started(event: any){

        d3.select(this).raise()
          .attr("transform", "translate(" + d3.event.x + ", 0)");
        svg.selectAll("rect")
          .style("fill", function (d) { return (this as any).x.baseVal.value < d3.event.x ? "lightsteelblue": "steelblue"})
      }


    let lineStartGroup = outerSvg.append("g")
      .call(d3.drag().on("drag", started))
      .style("cursor", "ew-resize");

    let lineStart = lineStartGroup
      .append("line")
      .attr("x1", x(geneWeights.min))
      .attr("y1", 0)
      .attr("x2", x(geneWeights.min))
      .attr("y2", height + 50)
      .attr("stroke", "green")
      .attr("stroke-width", 5)



    lineStartGroup.append("path")
      .attr("transform", function(d) { return "translate(6, 15) rotate(90) scale(0.5)"; })
      .attr("stroke", "black")
      .attr("fill", "green")
      .attr("d", d3.symbol().type((d3.symbolTriangle)));

    lineStartGroup.append("path")
      .attr("transform", function(d) { return "translate(-6, 15) rotate(-90) scale(0.5)"; })
      .attr("stroke", "black")
      .attr("fill", "green")
      .attr("d", d3.symbol().type((d3.symbolTriangle)));
  }

  ngOnInit() {
    this.geneWeightsService.getGeneWeights().subscribe(
      (geneWeights) => {
        this.geneWeights = geneWeights;
        this.redrawHistogram(geneWeights[0]);
        console.log(this.geneWeights);
      });
  }
}
