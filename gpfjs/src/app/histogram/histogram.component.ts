import { Input, Component, OnInit, ViewChild, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { GeneWeights } from '../gene-weights/gene-weights';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-histogram',
  templateUrl: './histogram.component.html'
})
export class HistogramComponent  {
  @Output() rangeStartChange = new EventEmitter();
  @Input() rangeStart: number;
  @Output() rangeEndChange = new EventEmitter();
  @Input() rangeEnd: number;

  @Input() width: number;
  @Input() height: number;
  @Input() marginLeft = 100;
  @Input() marginTop = 30;
  @ViewChild('histogramContainer') histogramContainer: any;

  @Input() domainMin: number;
  @Input() domainMax: number;
  @Input() bins: Array<number>;
  @Input() bars: Array<number>;

  @Input() leftRangeText: string;
  @Input() centerRangeText: string;
  @Input() rightRangeText: string;

  private xScale: d3.ScaleLinear<number, number>;
  private barsTotalSum: number;
  private barWidth: number;

  private svg: any;
  ngOnChanges(changes: SimpleChanges) {
    if ("domainMin" in changes || "domainMax" in changes || "bins" in changes || "bars" in changes) {
      d3.select(this.histogramContainer.nativeElement).selectAll("g").remove();
      d3.select(this.histogramContainer.nativeElement).selectAll("rect").remove();
      this.redrawHistogram();
    }

    if ("rangeStart" in changes || "rangeEnd" in changes) {
      this.estimateRangeTexts();
      this.svg.selectAll("rect").style("fill", (d, index, objects) => {
        return objects[index].x.baseVal.value < this.rangeStartX
            || objects[index].x.baseVal.value > this.rangeEndX
             ? "lightsteelblue": "steelblue"})
    }
  }

  formatEstimateText(count: number) {
    let perc = count/this.barsTotalSum * 100
    return "~" + count.toFixed(0) + " (" +  perc.toFixed(2) +"%)";
  }

  estimateRangeTexts() {
    let rangeStartIndex = this.rangeStartX/this.barWidth;
    let rangeEndIndex = this.rangeEndX/this.barWidth;

    let beforeRange = d3.sum(this.bars.slice(0, rangeStartIndex));
    let insideRange = d3.sum(this.bars.slice(rangeStartIndex, rangeEndIndex));
    let afterRange = d3.sum(this.bars.slice(rangeEndIndex));

    this.leftRangeText = this.formatEstimateText(beforeRange);
    this.centerRangeText = this.formatEstimateText(insideRange);
    this.rightRangeText = this.formatEstimateText(afterRange);
  }

  redrawHistogram() {
    this.barsTotalSum = d3.sum(this.bars);

    let barsBinsArray = [];
    for (var i = 0; i < this.bars.length; i++) {
      barsBinsArray[i] = {
        bin: this.bins[i],
        bar: this.bars[i]
      };
    }

    let width = 450;
    let height = 50;
    this.barWidth = width / this.bars.length;
    let svg = d3.select(this.histogramContainer.nativeElement)

    this.xScale = d3.scaleLinear()
      .domain([this.domainMin, this.domainMax])
      .rangeRound([0, width]);

    var y = d3.scaleLinear().range([height, 0]);

    y.domain([0, d3.max(this.bars)]);
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
      .attr("width", this.barWidth)
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
    return this.xScale(this.domainMin);
  }

  get maxX() {
    return this.xScale(this.domainMax);
  }

}
