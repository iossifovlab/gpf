import { Input, Component, OnInit, ViewChild, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { GeneWeights } from '../gene-weights/gene-weights';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-histogram',
  templateUrl: './histogram.component.html'
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

  private xScale: d3.ScaleLinear<number, number>;
  private barsTotalSum: number;
  private barWidth: number;

  private lastValidStart = 0;
  private lastValidEnd = 0;

  private svg: any;

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
    if (!this.rangeStart || !this.rangeEnd || !this.xScale) {
      return;
    }

    this.estimateRangeTexts();
    this.svg.selectAll("rect").style("fill", (d, index, objects) => {
      return objects[index].x.baseVal.value < this.rangeStartX
          || objects[index].x.baseVal.value > this.rangeEndX
           ? "lightsteelblue": "steelblue"})
  }

  formatEstimateText(count: number, estimate: boolean = true) {
    let perc = count/this.barsTotalSum * 100
    let string = estimate ? "~" : "";
    return string + count.toFixed(0) + " (" +  perc.toFixed(2) +"%)";
  }

  estimateRangeTexts() {
    let rangeStartIndex = this.rangeStartX/this.barWidth;
    let rangeEndIndex = this.rangeEndX/this.barWidth;

    let beforeRangeCount = d3.sum(this.bars.slice(0, rangeStartIndex));
    let insideRangeCount = d3.sum(this.bars.slice(rangeStartIndex, rangeEndIndex));
    let afterRangeCount  = d3.sum(this.bars.slice(rangeEndIndex));

    this.beforeRangeText = this.formatEstimateText(beforeRangeCount);
    this.insideRangeText = this.formatEstimateText(insideRangeCount);
    this.afterRangeText  = this.formatEstimateText(afterRangeCount);
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

    this.onRangeChange();
  }

  get rangeStartX() {
    let rangeStart = this.rangeStart;
    if (rangeStart > this.rangeEnd
        || rangeStart > this.domainMax
        || rangeStart < this.domainMin ) {
      rangeStart = this.lastValidStart;
    }
    else {
      this.lastValidStart = rangeStart;
    }
    return this.xScale(rangeStart);
  }

  set rangeStartX(x: number) {
    this.rangeStart = this.xScale.invert(x);
  }

  get rangeEndX() {
    let rangeEnd = this.rangeEnd;
    if (rangeEnd > this.domainMax
        || rangeEnd < this.rangeStart
        || rangeEnd < this.domainMin ) {
      rangeEnd = this.lastValidEnd;
    }
    else {
      this.lastValidEnd = rangeEnd;
    }
    return this.xScale(rangeEnd);
  }

  set rangeEndX(x: number) {
    this.rangeEnd = this.xScale.invert(x);
  }

  get minX() {
    return this.xScale(this.domainMin);
  }

  get maxX() {
    return this.xScale(this.domainMax);
  }

  @Input()
  set rangeStart(rangeStart) {
    this.internalRangeStart = rangeStart;
    this.onRangeChange();
    this.rangeStartChange.emit(this.internalRangeStart);
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  @Input()
  set rangeEnd(rangeEnd) {
    this.internalRangeEnd = rangeEnd;
    this.onRangeChange();
    this.rangeEndChange.emit(this.internalRangeEnd);
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }

}
