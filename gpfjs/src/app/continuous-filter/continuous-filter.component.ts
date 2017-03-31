import { Component, OnInit, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { HistogramData } from '../measures/measures'

@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html',
  styleUrls: ['./continuous-filter.component.css']
})
export class ContinuousFilterComponent implements OnInit {
  @Input() datasetId: string;
  @Input() measureName: string;
  histogramData: HistogramData;

  rangeStart: number;
  rangeEnd: number;

  rangesCounts = [0, 0, 0];

  constructor(
    private measuresService: MeasuresService
  ) { }

  ngOnInit() {
  }

  ngOnChanges() {
    if (this.datasetId && this.measureName) {
      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName).subscribe(
        (histogramData) => {
          this.histogramData = histogramData;
          this.rangeStart = histogramData.min;
          this.rangeEnd = histogramData.max;
        }
      )
    }
  }

}
