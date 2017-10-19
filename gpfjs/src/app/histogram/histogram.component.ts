import { Input, Component, OnInit, ViewChild, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { GeneWeights } from '../gene-weights/gene-weights';
import * as d3 from 'd3';
import { Subject } from 'rxjs/Subject';

@Component({
  selector: 'gpf-histogram',
  templateUrl: './histogram.component.html',
  styleUrls: ['./histogram.component.css']
})
export class HistogramComponent  {
  private rangeStartSubject = new Subject<number>();
  private rangeEndSubject = new Subject<number>();

  private internalRangeStart: number;
  private internalRangeEnd: number;

  @Output() rangeStartChange = new EventEmitter();
  @Output() rangeEndChange = new EventEmitter();

  @Input() width: number;
  @Input() height: number;
  @Input() marginLeft = 100;
  @Input() marginTop = 10;
  @ViewChild('histogramContainer') histogramContainer: any;

  @Input() bins: Array<number>;
  @Input() bars: Array<number>;

  @Input() rangesCounts: Array<number>;

  @Input() logScaleY = false;
  @Input() showCounts = true;
  @Input() xLabels: Array<number>

  beforeRangeText: string;
  insideRangeText: string;
  afterRangeText: string;

  xScale: d3.ScaleBand< string>;
  private barsTotalSum: number;

  private lastValidStart = 0;
  private lastValidEnd = 0;

  private svg: any;

  scaledBins: Array<number>;

  ngOnInit() {
      this.rangeStartSubject.debounceTime(100).distinctUntilChanged().subscribe((start) => this.rangeStartChange.emit(start))
      this.rangeEndSubject.debounceTime(100).distinctUntilChanged().subscribe((end) => this.rangeEndChange.emit(end))
  }

  ngOnChanges(changes: SimpleChanges) {
    if ("bins" in changes || "bars" in changes) {
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

    if (this.showCounts) {
        let string = estimate ? "~" : "";
        return string + count.toFixed(0) + " (" +  perc.toFixed(2) +"%)";
    }
    else {
        return perc.toFixed(2) + "%";
    }
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

    let svg = d3.select(this.histogramContainer.nativeElement)

    this.xScale = d3.scaleBand()
      .paddingInner(0.1)
      .domain(Array.from(this.bins.keys()).map(x => x.toString()))
      .range([0, width]);

    var y = this.logScaleY ?  d3.scaleLog() : d3.scaleLinear();
    y.range([height, 0]).domain([1, d3.max(this.bars)]);

    // Add the x Axis
    let labels;
    if (this.xLabels) {
        labels = this.xLabels
    }
    else {
        labels = d3.ticks(this.bins[0], this.bins[this.bins.length - 1], 10)
    }

    let values = labels.map(x => this.getClosestIndexByValue(x))

    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(this.xScale).tickValues(values as any).tickFormat((d,i) => labels[i] as any))

    let leftAxis = d3.axisLeft(y);
    leftAxis.ticks(3).tickFormat(d3.format(".0f"));
    svg.append("g")
        .call(leftAxis);
    svg.selectAll("bar")
      .data(barsBinsArray)
      .enter().append("rect")
      .style("fill", "steelblue")
      .attr("x", (d: any) => this.xScale(d.index.toString()))
      .attr("width", this.xScale.bandwidth())
      .attr("y", (d: any) => d.bar == 0 ? 0 : y(d.bar))
      .attr("height", (d: any) => height - (d.bar == 0 ? 0 : y(d.bar)));
    this.svg = svg;

    this.onRangeChange();
    this.scaledBins = barsBinsArray.map(d => d.bin == 0 ? 0 : this.xScale(d.bin));
    this.selectedEndIndex = this.bars.length - 1;
  }

  @Input()
  set rangeStart(rangeStart: any) {
    this.internalRangeStart = parseFloat(rangeStart);
    if (isNaN(this.internalRangeStart)) {
        this.internalRangeStart = null
    }
    this.onRangeChange();
    this.rangeStartSubject.next(this.internalRangeStart)
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  @Input()
  set rangeEnd(rangeEnd: any) {
    this.internalRangeEnd = parseFloat(rangeEnd);
    if (isNaN(this.internalRangeEnd)) {
        this.internalRangeEnd = null
    }
    this.onRangeChange();
    this.rangeEndSubject.next(this.internalRangeEnd)
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }


  startStepUp(event: any) {
      this.selectedStartIndex += 1
  }

  startStepDown(event: any) {
      this.selectedStartIndex -= 1
  }

  endStepUp(event: any) {
      this.selectedEndIndex += 1
  }

  endStepDown(event: any) {
      this.selectedEndIndex -= 1
  }

  set selectedStartIndex(index: number) {
    if (index < 0 || index > this.selectedEndIndex) return;
    this.internalRangeStart = this.round(this.bins[index])
    this.onRangeChange();
    this.rangeStartSubject.next(this.internalRangeStart)
  }

  get selectedStartIndex() {
      return this.getClosestIndexByValue(this.rangeStart)
  }

  set selectedEndIndex(index: number) {
    if (index < this.selectedStartIndex || index >= this.bars.length) return;
    this.internalRangeEnd = this.round(this.bins[index + 1])
    this.onRangeChange();
    this.rangeEndSubject.next(this.internalRangeEnd)
  }

  get selectedEndIndex() {
      return this.getClosestIndexByValue(this.rangeEnd) - 1
  }

  round(value: number): number{
      return Math.round(value * 1000) / 1000
  }

  getClosestIndexByX(x) {
      //Domain uses bins count which is larger than bars by 1 element
      let maxIndex = this.xScale.domain().length - 2
      for(var i  = 1; i <= maxIndex; i++) {
          var prev_val = (i - 1) * this.xScale.step()
          var curr_val = i * this.xScale.step()
          if (curr_val> x) {
              var prev = Math.abs(x - prev_val)
              var curr = Math.abs(x - curr_val)
              return prev < curr ? i - 1 : i;
          }
      }
      return maxIndex
  }

  getClosestIndexByValue(val) {
      for(var i  = 1; i < this.bins.length; i++) {
          if (this.round(this.bins[i]) >= val) {
              var prev = Math.abs(val - this.bins[i - 1])
              var curr = Math.abs(val - this.bins[i])
              return prev < curr ? i - 1 : i;
          }
      }
      return 0
  }

  startXChange(newPositionX) {
      this.selectedStartIndex = this.getClosestIndexByX(newPositionX);
  }

  endXChange(newPositionX) {
      this.selectedEndIndex = this.getClosestIndexByX(newPositionX);
  }
}
