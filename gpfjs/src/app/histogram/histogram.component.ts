import { Input, Component, OnInit, ViewChild, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { GeneWeights } from '../gene-weights/gene-weights';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-histogram',
  templateUrl: './histogram.component.html',
  styleUrls: ['./histogram.component.css']
})
export class HistogramComponent  {
  private internalRangeStart: number;
  private internalRangeEnd: number;

  @Output() rangeStartChange = new EventEmitter();
  @Output() rangeEndChange = new EventEmitter();

  @Input() width: number;
  @Input() height: number;
  @Input() marginLeft = 100;
  @Input() marginTop = 10;
  @ViewChild('histogramContainer') histogramContainer: any;

  @Input() domainMin: number;
  @Input() domainMax: number;
  @Input() bins: Array<number>;
  @Input() bars: Array<number>;

  @Input() rangesCounts: Array<number>;

  beforeRangeText: string;
  insideRangeText: string;
  afterRangeText: string;

  private xScale: d3.ScaleBand< string>;
  private barsTotalSum: number;
  private barWidth: number;

  private lastValidStart = 0;
  private lastValidEnd = 0;

  private svg: any;

  scaledBins: Array<number>;
  internalSelectedStartIndex = 0;
  internalSelectedEndIndex = 0;

  ngOnChanges(changes: SimpleChanges) {
    if ("domainMin" in changes || "domainMax" in changes || "bins" in changes || "bars" in changes) {
      d3.select(this.histogramContainer.nativeElement).selectAll("g").remove();
      d3.select(this.histogramContainer.nativeElement).selectAll("rect").remove();
      this.redrawHistogram();
    }

    if ("rangesCounts" in changes ) {
      if (this.rangesCounts && this.rangesCounts.length == 3) {
        this.beforeRangeText = this.formatEstimateText(this.rangesCounts[0], false);
        this.insideRangeText = this.formatEstimateText(this.rangesCounts[1], false);
        this.afterRangeText  = this.formatEstimateText(this.rangesCounts[2], false);
      }
    }
  }

  onRangeChange() {
    if (!this.xScale) {
      return;
    }

    this.estimateRangeTexts();
    this.svg.selectAll("rect").style("fill", (d, index, objects) => {
      return d.index < this.selectedStartIndex
          || d.index > this.selectedEndIndex
           ? "lightsteelblue": "steelblue"})
  }

  formatEstimateText(count: number, estimate: boolean = true) {
    let perc = count/this.barsTotalSum * 100
    let string = estimate ? "~" : "";
    return string + count.toFixed(0) + " (" +  perc.toFixed(2) +"%)";
    //return perc.toFixed(5) + "%";
  }

  estimateRangeTexts() {
    let beforeRangeCount = d3.sum(this.bars.slice(0, this.selectedStartIndex));
    let insideRangeCount = d3.sum(this.bars.slice(this.selectedStartIndex, this.selectedEndIndex + 1));
    let afterRangeCount  = d3.sum(this.bars.slice(this.selectedEndIndex + 1));

    this.beforeRangeText = this.formatEstimateText(beforeRangeCount);
    this.insideRangeText = this.formatEstimateText(insideRangeCount);
    this.afterRangeText  = this.formatEstimateText(afterRangeCount);
  }

  redrawHistogram() {
    this.barsTotalSum = d3.sum(this.bars);

    let barsBinsArray = [];
    for (var i = 0; i < this.bars.length; i++) {
      barsBinsArray[i] = {
        index: i,
        bin: this.bins[i],
        bar: this.bars[i]
      };
    }

    let width = 400.0;
    let height = 50;
    this.barWidth = width / this.bars.length - 2;
    console.log(this.barWidth, width, this.bars.length)
    let svg = d3.select(this.histogramContainer.nativeElement)

    this.xScale = d3.scaleBand()
      .domain(Array.from(this.bars.keys()).map(x => x.toString()))
      .range([0, width]);

    var y = d3.scaleLog().range([height, 0]);

    y.domain([1, d3.max(this.bars)]);

    let labels = d3.range(-2, 2.1, 1).map(x => Math.pow(10, x))
    // Add the x Axis
    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(this.xScale).tickValues(["0", "26", "76"]).tickFormat((d,i) => this.bins[parseInt(d)] as any))

    let leftAxis = d3.axisLeft(y);
    leftAxis.ticks(3).tickFormat(d3.format(".0f"));
    svg.append("g")
        .call(leftAxis);

    svg.selectAll("bar")
      .data(barsBinsArray)
      .enter().append("rect")
      .style("fill", "steelblue")
      .attr("x", (d: any) => this.xScale(d.index.toString()))
      .attr("width", this.barWidth)
      .attr("y", function(d: any) { return y(d.bar); })
      .attr("height", function(d: any) { return height - y(d.bar); });
    this.svg = svg;

    this.onRangeChange();
    this.scaledBins = barsBinsArray.map(d => d.bin == 0 ? 0 : this.xScale(d.bin));
    this.selectedEndIndex = this.bars.length - 1;
  }

  @Input()
  set rangeStart(rangeStart) {
    this.internalRangeStart = rangeStart;
    for(var i  = 1; i < this.bins.length; i++) {
        if (this.bins[i] > rangeStart) {
            var prev = Math.abs(rangeStart - this.bins[i - 1])
            var curr = Math.abs(rangeStart - this.bins[i])
            this.internalSelectedStartIndex = prev < curr ? i - 1 : i;
            break;
        }
    }
    this.onRangeChange();
    this.rangeStartChange.emit(this.internalRangeStart);
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  @Input()
  set rangeEnd(rangeEnd) {
    this.internalRangeEnd = rangeEnd;
    for(var i  = 1; i < this.bins.length; i++) {
        if (this.bins[i] > rangeEnd) {
            var prev = Math.abs(rangeEnd - this.bins[i - 1])
            var curr = Math.abs(rangeEnd - this.bins[i])
            this.internalSelectedEndIndex = prev < curr ? i - 1 : i;
            break;
        }
    }
    this.onRangeChange();
    this.rangeEndChange.emit(this.internalRangeEnd);
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }


  startStepUp() {
      this.selectedStartIndex += 1
  }

  startStepDown() {
      this.selectedStartIndex -= 1
  }

  endStepUp() {
      this.selectedEndIndex += 1
  }

  endStepDown() {
      this.selectedEndIndex -= 1
  }

  set selectedStartIndex(index: number) {
    this.internalSelectedStartIndex = index
    this.internalRangeStart = Math.round(this.bins[index] * 1000) / 1000
    this.onRangeChange();
    this.rangeStartChange.emit(this.internalRangeStart);
  }

  get selectedStartIndex() {
    return this.internalSelectedStartIndex
  }

  set selectedEndIndex(index: number) {
    this.internalSelectedEndIndex = index
    this.internalRangeEnd = Math.round(this.bins[index + 1] * 1000) / 1000
    this.onRangeChange();
    this.rangeEndChange.emit(this.internalRangeEnd);
  }

  get selectedEndIndex() {
    return this.internalSelectedEndIndex
  }

}
