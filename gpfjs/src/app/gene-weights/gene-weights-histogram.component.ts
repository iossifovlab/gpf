import { Input, Component, OnInit, ViewChild, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { GeneWeights } from './gene-weights';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-gene-weights-histogram',
  templateUrl: './gene-weights-histogram.component.html'
})
export class GeneWeightsHistogramComponent  {
  @Output() rangeStartChange = new EventEmitter();
  @Input() rangeStart: number;
  @Output() rangeEndChange = new EventEmitter();
  @Input() rangeEnd: number;

  @Input() width: number;
  @Input() height: number;
  @Input() marginLeft = 100;
  @Input() marginTop = 30;
  @ViewChild('histogramContainer') histogramContainer: any;
  @Input()  geneWeights: GeneWeights;

  private xScale: d3.ScaleLinear<number, number>;

  private svg: any;
  ngOnChanges(changes: SimpleChanges) {
    if ("geneWeights" in changes) {
      d3.select(this.histogramContainer.nativeElement).selectAll("g").remove();
      d3.select(this.histogramContainer.nativeElement).selectAll("rect").remove();
      this.redrawHistogram(this.geneWeights);
    }

    if ("rangeStart" in changes || "rangeEnd" in changes) {
      this.svg.selectAll("rect").style("fill", (d, index, objects) => {
        return objects[index].x.baseVal.value < this.rangeStartX
            || objects[index].x.baseVal.value > this.rangeEndX
             ? "lightsteelblue": "steelblue"})
    }
  }

  redrawHistogram(geneWeights: GeneWeights) {
    let barsBinsArray = [];
    for (var i = 0; i < geneWeights.bars.length; i++) {
      barsBinsArray[i] = {
        bin: geneWeights.bins[i],
        bar: geneWeights.bars[i]
      };
    }

    let width = 450;
    let height = 50;
    let barWidth = width / geneWeights.bars.length;
    let svg = d3.select(this.histogramContainer.nativeElement)

    this.xScale = d3.scaleLinear()
      .domain([geneWeights.min, geneWeights.max])
      .rangeRound([0, width]);

    var y = d3.scaleLinear().range([height, 0]);

    y.domain([0, d3.max(geneWeights.bars)]);
    // Add the x Axis
    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(this.xScale));

    let leftAxis = d3.axisLeft(y);
    leftAxis.ticks(5);
    svg.append("g")
        .call(leftAxis);

    svg.selectAll("bar")
      .data(barsBinsArray)
      .enter().append("rect")
      .style("fill", "steelblue")
      .attr("x", (d: any) => { return this.xScale(d.bin);})
      .attr("width", barWidth)
      .attr("y", function(d: any) { return y(d.bar); })
      .attr("height", function(d: any) { return height - y(d.bar); });
    this.svg = svg;
  }

  get rangeStartX() {
    return this.xScale(this.rangeStart);
  }

  set rangeStartX(x: number) {
    this.rangeStart = this.xScale.invert(x);
    this.rangeStartChange.emit(this.rangeStart);
  }

  get rangeEndX() {
    return this.xScale(this.rangeEnd);
  }

  set rangeEndX(x: number) {
    this.rangeEnd = this.xScale.invert(x);
    this.rangeEndChange.emit(this.rangeEnd);
  }

  get minX() {
    return this.xScale(this.geneWeights.min);
  }

  get maxX() {
    return this.xScale(this.geneWeights.max);
  }

}
