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
  @Input() centerLabels: boolean;
  @Input() showMinMaxInput: boolean;

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
      this.rangeStartSubject
      .debounceTime(100)
      .distinctUntilChanged()
      .subscribe((start) => {
          let step = Math.abs(this.bins[1] - this.bins[0]) / 1e10;
          if (Math.abs(start - this.bins[0]) < step) {
            this.rangeStartChange.emit(null)
          }
          else {
            this.rangeStartChange.emit(start)
          }
      })

      this.rangeEndSubject
      .debounceTime(100)
      .distinctUntilChanged()
      .subscribe((end) => { 
          let step = Math.abs(this.bins[this.bins.length - 1] 
            - this.bins[this.bins.length - 2]) / 1e10;
          if (Math.abs(end - this.bins[this.bins.length - 1]) < step) {
            this.rangeEndChange.emit(null)
          }
          else {
            this.rangeEndChange.emit(end)
          }
      })
  }

  ngOnChanges(changes: SimpleChanges) {
    if ("bins" in changes || "bars" in changes) {
      d3.select(this.histogramContainer.nativeElement).selectAll("g").remove();
      d3.select(this.histogramContainer.nativeElement).selectAll("rect").remove();
      this.redrawHistogram();
      this.rangeStart = null;
      this.rangeEnd = null;
    }

    if ("rangesCounts" in changes ) {
      if (this.rangesCounts && this.rangesCounts.length == 3) {
        this.beforeRangeText = this.formatEstimateText(this.rangesCounts[0], false);
        this.insideRangeText = this.formatEstimateText(this.rangesCounts[1], false);
        this.afterRangeText  = this.formatEstimateText(this.rangesCounts[2], false);
      }
    }
  }

  get showMinMaxInputWithDefaultValue() {
    if (this.showMinMaxInput === undefined) {
        if (this.bins.length < 10) {
            return false;
        }
        else {
            return true;
        }
    }
    return this.showMinMaxInput;
  }

  get centerLabelsWithDefaultValue() {
    if (this.centerLabels === undefined) {
        if (this.bins.length < 10) {
            return true;
        }
        else {
            return false;
        }
    }
    return this.centerLabels;
  }

  get xLabelsWithDefaultValue() {
    if (this.xLabels === undefined) {
        if (this.bins.length < 10) {
            return this.bins.slice(0, -1);
        }
        else {
            return d3.ticks(this.bins[0], this.bins[this.bins.length - 1], 10);
        }
    }
    return this.xLabels;
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
      .padding(0.1)
      .domain(Array.from(this.bars.keys()).map(x => x.toString()))
      .range([0, width]);

    var y = this.logScaleY ?  d3.scaleLog() : d3.scaleLinear();
    y.range([height, 0]).domain([1, d3.max(this.bars)]);

    this.redrawXAxis(svg, width, height);

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
      .attr("y", (d: any) => d.bar == 0 ? height : y(d.bar))
      .attr("height", (d: any) => d.bar == 0 ? 0 : height -  y(d.bar));
    this.svg = svg;

    this.onRangeChange();
    this.scaledBins = barsBinsArray.map(d => d.bin == 0 ? 0 : this.xScale(d.bin));
    this.selectedEndIndex = this.bars.length - 1;
  }

  redrawXAxis(svg, width, height) {
    let axisX = [0];
    let axisVals = [];
    for(var i  = 0; i < this.bins.length - 1; i++) {
        var leftX;
        if (this.centerLabelsWithDefaultValue) {
            leftX = this.xScale(i.toString()) + this.xScale.bandwidth() / 2;
        }
        else {
            leftX = this.xScale(i.toString()) - this.xScale.step() * this.xScale.paddingOuter() / 2;
        }
        axisX.push(leftX);
        axisVals.push(this.bins[i]);
    }

    if (this.centerLabelsWithDefaultValue) {
        axisX.push(width);
        axisVals.push(Number.POSITIVE_INFINITY);
    } 
    else {
        axisX.push(width);
        axisVals.push(this.bins[this.bins.length - 1]);
    }
    var scaleXAxis = d3.scaleThreshold().range(axisX).domain(axisVals);

    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(scaleXAxis).tickValues(this.xLabelsWithDefaultValue as any).tickFormat((d,i) => this.xLabelsWithDefaultValue[i] as any))
  }

  @Input()
  set rangeStart(rangeStart: any) {
    if (rangeStart == null) {
        this.internalRangeStart = this.bins[0]
    }
    else {
        this.internalRangeStart = parseFloat(rangeStart);
        if (isNaN(this.internalRangeStart)) {
            this.internalRangeStart = null
        }
    }
    this.onRangeChange();
    this.rangeStartSubject.next(this.internalRangeStart)
  }

  get rangeStart() {
    return this.internalRangeStart;
  }
 
  @Input()
  set rangeEnd(rangeEnd: any) {
    if (rangeEnd == null) {
        this.internalRangeEnd = this.bins[this.bins.length - 1]
    }
    else {
        this.internalRangeEnd = parseFloat(rangeEnd);
        if (isNaN(this.internalRangeEnd)) {
            this.internalRangeEnd = null
        }
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
      let maxIndex = this.bins.length - 2;
      return Math.min(maxIndex, this.getClosestIndexByValue(this.rangeStart));
  }

  set selectedEndIndex(index: number) {
    if (index < this.selectedStartIndex || index >= this.bars.length) return;
    this.internalRangeEnd = this.round(this.bins[index + 1])
    this.onRangeChange();
    this.rangeEndSubject.next(this.internalRangeEnd)
  }

  get selectedEndIndex() {
      return this.getClosestIndexByValue(this.rangeEnd) - 1;
  }

  round(value: number): number{
      return Math.round(value * 1000) / 1000
  }

  getClosestIndexByX(x) {
      //Domain uses bins count which is larger than bars by 1 element
      let maxIndex = this.xScale.domain().length - 1
      for(var i  = 1; i <= maxIndex; i++) {
          var prev_val = (i - 1) * this.xScale.step()
          var curr_val = i * this.xScale.step()
          if (curr_val> x) {
              var prev = Math.abs(x - prev_val)
              var curr = Math.abs(x - curr_val)
              return prev < curr ? i - 1 : i;
          }
      }
      return maxIndex - 1;
  }

  getClosestIndexByValue(val) {
      for(var i  = 1; i < this.bins.length - 1; i++) {
          if (this.round(this.bins[i]) >= val) {
              var prev = Math.abs(val - this.bins[i - 1])
              var curr = Math.abs(val - this.bins[i])
              return prev < curr ? i - 1 : i;
          }
      }
      return this.bins.length - 1
  }

  startXChange(newPositionX) {
      this.selectedStartIndex = this.getClosestIndexByX(newPositionX);
  }

  endXChange(newPositionX) {
      this.selectedEndIndex = this.getClosestIndexByX(newPositionX);
  }
}
