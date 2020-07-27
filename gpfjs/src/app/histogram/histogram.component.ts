import { Input, Component, OnInit, OnChanges, ViewChild, Output, EventEmitter, SimpleChanges } from '@angular/core';
import * as d3 from 'd3';
// tslint:disable-next-line:import-blacklist
import { Subject } from 'rxjs';
import 'rxjs/add/operator/debounceTime';


@Component({
  selector: 'gpf-histogram',
  templateUrl: './histogram.component.html',
  styleUrls: ['./histogram.component.css']
})
export class HistogramComponent implements OnInit, OnChanges {
  private rangeStartSubject = new Subject<number>();
  private rangeEndSubject = new Subject<number>();

  private internalRangeStart: number;
  private internalRangeEnd: number;

  private internalRangeStartField: number;
  private internalRangeEndField: number;

  @Output() rangeStartChange = new EventEmitter();
  @Output() rangeEndChange = new EventEmitter();

  @Input() width: number;
  @Input() height: number;
  @Input() marginLeft = 100;
  @Input() marginTop = 10;
  @ViewChild('histogramContainer', {static: true}) histogramContainer: any;

  @Input() bins: Array<number>;
  @Input() bars: Array<number>;
  @Input() domainMin: number;
  @Input() domainMax: number;

  @Input() rangesCounts: Array<number>;

  @Input() logScaleX = false;
  @Input() logScaleY = false;
  @Input() showCounts = true;
  @Input() xLabels: Array<number>;
  @Input() centerLabels: boolean;
  @Input() showMinMaxInput: boolean;

  beforeRangeText: string;
  insideRangeText: string;
  afterRangeText: string;

  xScale: d3.ScaleBand<string>;
  private barsTotalSum: number;

  private lastValidStart = 0;
  private lastValidEnd = 0;

  private svg: any;

  scaledBins: Array<number>;
  private resetRange = false;

  ngOnInit() {
      this.rangeStartSubject
      .debounceTime(100)
      .subscribe((start) => {
          const step = Math.abs(this.bins[1] - this.bins[0]) / 1e10;
          if (Math.abs(start - this.bins[0]) < step) {
            this.rangeStartChange.emit(null);
          } else {
            this.rangeStartChange.emit(start);
          }
      });

      this.rangeEndSubject
      .debounceTime(100)
      .subscribe((end) => {
          const step = Math.abs(this.bins[this.bins.length - 1]
            - this.bins[this.bins.length - 2]) / 1e10;
          if (Math.abs(end - this.bins[this.bins.length - 1]) < step) {
            this.rangeEndChange.emit(null);
          } else {
            this.rangeEndChange.emit(end);
          }
      });
  }

  ngOnChanges(changes: SimpleChanges) {
    if ('bins' in changes || 'bars' in changes) {
      const bins: Array<number> = [];
      const bars: Array<number> = [];
      for (let i  = 0; i < this.bins.length; i++) {
        if (this.bins[i] < this.domainMin || this.bins[i] > this.domainMax) {
          continue;
        }
        bins.push(this.bins[i]);
        bars.push(this.bars[i]);
      }
      this.bins = bins;
      this.bars = bars;
      d3.select(this.histogramContainer.nativeElement).selectAll('g').remove();
      d3.select(this.histogramContainer.nativeElement).selectAll('rect').remove();
      this.redrawHistogram();
      if (this.resetRange) {
        this.rangeStart = null;
        this.rangeEnd = null;
      }
      this.resetRange = true;
    }

    if ('rangesCounts' in changes) {
      if (this.rangesCounts && this.rangesCounts.length === 3) {
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
        } else {
            return true;
        }
    }
    return this.showMinMaxInput;
  }

  get centerLabelsWithDefaultValue() {
    if (this.centerLabels === undefined) {
        if (this.bins.length < 10) {
            return true;
        } else {
            return false;
        }
    }
    return this.centerLabels;
  }

  get xLabelsWithDefaultValue() {
    if (this.xLabels === undefined) {
      if (this.bins.length < 10) {
        return this.bins.slice(0, -1);
      } else {
        if (!this.logScaleX) {
          return d3.ticks(this.bins[0], this.bins[this.bins.length - 1], 10);
        }
        const domainMin = this.bins[0] === 0.0 ? this.bins[1] : this.bins[0];
        const domainMax = this.bins[this.bins.length - 1];

        const magnitudeMin = Math.log10(domainMin);
        const magnitudeMax = Math.log10(domainMax);
        const count = Math.min(10, Math.floor(Math.abs(magnitudeMax - magnitudeMin)));

        return d3.scaleLog().domain([domainMin, domainMax]).ticks(count);
      }
    }
    return this.xLabels;
  }

  onRangeChange() {
    if (!this.xScale) {
      return;
    }

    this.estimateRangeTexts();
    this.colorBars();
  }

  colorBars() {
    this.svg.selectAll('rect').style('fill', (d, index, objects) => {
      return d.index < this.selectedStartIndex
          || d.index > this.selectedEndIndex
           ? 'lightsteelblue' : 'steelblue';
    });
  }

  formatEstimateText(count: number, estimate = true) {
    const perc = count / this.barsTotalSum * 100;

    if (this.showCounts) {
        const string = estimate ? '~' : '';
        return string + count.toFixed(0) + ' (' +  perc.toFixed(2) + '%)';
    } else {
        return perc.toFixed(2) + '%';
    }
  }

  estimateRangeTexts() {
    const beforeRangeCount = d3.sum(this.bars.slice(0, this.selectedStartIndex));
    const insideRangeCount = d3.sum(this.bars.slice(this.selectedStartIndex, this.selectedEndIndex + 1));
    const afterRangeCount  = d3.sum(this.bars.slice(this.selectedEndIndex + 1));

    this.beforeRangeText = this.formatEstimateText(beforeRangeCount);
    this.insideRangeText = this.formatEstimateText(insideRangeCount);
    this.afterRangeText  = this.formatEstimateText(afterRangeCount);
  }

  redrawHistogram() {
    this.barsTotalSum = d3.sum(this.bars);

    const barsBinsArray = [];
    for (let i = 0; i < this.bars.length; i++) {
      barsBinsArray[i] = {
        index: i,
        bin: this.bins[i],
        bar: this.bars[i]
      };
    }

    const width = 450.0;
    const height = 50;

    const svg = d3.select(this.histogramContainer.nativeElement);

    this.xScale = d3.scaleBand()
      .padding(0.1)
      .domain(Array.from(this.bars.keys()).map(x => x.toString()))
      .range([0, width]);

    const y = this.logScaleY ?  d3.scaleLog() : d3.scaleLinear();
    y.range([height, 0]).domain([1, d3.max(this.bars)]);

    this.redrawXAxis(svg, width, height);

    const leftAxis = d3.axisLeft(y);
    leftAxis.ticks(3).tickFormat(d3.format('.0f'));
    svg.append('g')
        .call(leftAxis);
    svg.selectAll('bar')
      .data(barsBinsArray)
      .enter().append('rect')
      .style('fill', 'steelblue')
      .attr('x', (d: any) => this.xScale(d.index.toString()))
      .attr('width', this.xScale.bandwidth())
      .attr('y', (d: any) => d.bar === 0 ? height : y(d.bar))
      .attr('height', (d: any) => d.bar === 0 ? 0 : height -  y(d.bar));
    this.svg = svg;

    this.colorBars();
    this.scaledBins = barsBinsArray.map(d => d.bin === 0 ? 0 : this.xScale(d.bin));
  }

  redrawXAxis(svg, width, height) {
    const axisX = [0];
    const axisVals = [];
    for (let i  = 0; i < this.bins.length - 1; i++) {
        let leftX;
        if (this.centerLabelsWithDefaultValue) {
            leftX = this.xScale(i.toString()) + this.xScale.bandwidth() / 2;
        } else {
            leftX = this.xScale(i.toString()) - this.xScale.step() * this.xScale.paddingOuter() / 2;
        }
        axisX.push(leftX);
        axisVals.push(this.bins[i]);
    }

    if (this.centerLabelsWithDefaultValue) {
        axisX.push(width);
        axisVals.push(Number.POSITIVE_INFINITY);
    } else {
        axisX.push(width);
        axisVals.push(this.bins[this.bins.length - 1]);
    }
    const scaleXAxis = d3.scaleThreshold().range(axisX).domain(axisVals);

    svg.append('g')
      .attr('transform', 'translate(0,' + height + ')')
      .call(
        d3.axisBottom(scaleXAxis)
        .tickValues(this.xLabelsWithDefaultValue as any)
        .tickFormat((d, i) => this.xLabelsWithDefaultValue[i] as any));
  }

  @Input()
  set rangeStart(rangeStart: any) {
    if (rangeStart !== this.internalRangeStart) {
      this.setRangeStart(rangeStart);
      this.internalRangeStartField = Number(this.rangeStart.toFixed(4));
    }
  }

  setRangeStart(rangeStart: any) {
    if (rangeStart == null) {
        this.internalRangeStart = this.bins[0];
    } else {
        this.internalRangeStart = rangeStart;
    }
    this.onRangeChange();
    this.rangeStartSubject.next(this.internalRangeStart);
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  @Input()
  set rangeEnd(rangeEnd: any) {
    if (rangeEnd !== this.internalRangeEnd) {
      this.setRangeEnd(rangeEnd);
      this.internalRangeEndField = Number(this.rangeEnd.toFixed(4));
    }
  }

  setRangeEnd(rangeEnd: any) {
    if (rangeEnd == null) {
        this.internalRangeEnd = this.bins[this.bins.length - 1];
    } else {
        this.internalRangeEnd = rangeEnd;
    }
    this.onRangeChange();
    this.rangeEndSubject.next(this.internalRangeEnd);
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }

  set rangeStartWithoutNull(rangeStart: any) {
    const rangeStartFloat = parseFloat(rangeStart);
    if (!isNaN(rangeStartFloat)) {
      this.setRangeStart(parseFloat(rangeStart));
    } else {
      this.setRangeStart(null);
    }
  }

  get rangeStartWithoutNull() {
    return this.internalRangeStartField;
  }

  set rangeEndWithoutNull(rangeEnd: any) {
    const rangeEndFloat = parseFloat(rangeEnd);
    if (!isNaN(rangeEndFloat)) {
      this.setRangeEnd(parseFloat(rangeEnd));
    } else {
      this.setRangeEnd(null);
    }
  }

  get rangeEndWithoutNull() {
    return this.internalRangeEndField;
  }

  get min_value() {
    return Number(this.bins[0].toFixed(4));
  }

  get max_value() {
    return Number(this.bins[this.bins.length - 1].toFixed(4));
  }

  startStepUp(event: any) {
      this.selectedStartIndex += 1;
  }

  startStepDown(event: any) {
      this.selectedStartIndex -= 1;
  }

  endStepUp(event: any) {
      this.selectedEndIndex += 1;
  }

  endStepDown(event: any) {
      this.selectedEndIndex -= 1;
  }

  set selectedStartIndex(index: number) {
    if (index < 0 || index > this.selectedEndIndex) {
      return;
    }
    this.rangeStart = this.bins[index];
  }

  get selectedStartIndex() {
      if (this.rangeStart === null) {
        return 0;
      }
      const maxIndex = this.bins.length - 2;
      const closest = this.getClosestIndexByValue(this.rangeStart);
      return Math.min(maxIndex, closest);
  }

  set selectedEndIndex(index: number) {
    if (index < this.selectedStartIndex || index >= this.bars.length) {
      return;
    }
    this.rangeEnd = this.bins[index + 1];
  }

  get selectedEndIndex() {
      if (this.rangeEnd === null) {
        return this.bins.length - 2;
      }
      return Math.max(0, this.getClosestIndexByValue(this.rangeEnd) - 1);
  }

  getClosestIndexByX(x) {
      // Domain uses bins count which is larger than bars by 1 element
      const maxIndex = this.xScale.domain().length;
      for (let i  = 1; i < maxIndex; i++) {
          const prev_val = (i - 1) * this.xScale.step();
          const curr_val = i * this.xScale.step();
          if (curr_val > x) {
              const prev = Math.abs(x - prev_val);
              const curr = Math.abs(x - curr_val);
              return prev < curr ? i - 1 : i;
          }
      }
      return maxIndex - 1;
  }

  getClosestIndexByValue(val) {
      for (let i  = 1; i < this.bins.length - 1; i++) {
          if (this.bins[i] >= val) {
              const prev = Math.abs(val - this.bins[i - 1]);
              const curr = Math.abs(val - this.bins[i]);
              return prev < curr ? i - 1 : i;
          }
      }
      return this.bins.length - 1;
  }

  get startX() {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    return this.xScale(this.selectedStartIndex.toString()) - distBetweenBars / 2 - 1;
  }

  set startX(newPositionX) {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    this.selectedStartIndex = this.getClosestIndexByX(newPositionX + distBetweenBars / 2 + 1);
  }

  get endX() {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    return this.xScale(this.selectedEndIndex.toString()) + this.xScale.bandwidth() + distBetweenBars / 2 - 1;
  }

  set endX(newPositionX) {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    this.selectedEndIndex = this.getClosestIndexByX(newPositionX - this.xScale.bandwidth() - distBetweenBars / 2 + 1);
  }
}
