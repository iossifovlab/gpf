import { Component, Input } from '@angular/core';
import { GenotypeBrowser, MissenseMetric } from '../datasets/datasets';
import { MissenseScoresService } from './missense-scores.service'
import { MissenseScoresHistogramData } from './missense-scores';

@Component({
  selector: 'gpf-missense-scores',
  templateUrl: './missense-scores.component.html',
})
export class MissenseScoresComponent {
  @Input() genotypeBrowserConfig: GenotypeBrowser;
  private internalSelectedMetric: MissenseMetric;
  private histogramData: MissenseScoresHistogramData;

  constructor(
    private missenseScoresService: MissenseScoresService
  )  {}

  set selectedMetric(selectedMetric: MissenseMetric) {
    this.internalSelectedMetric = selectedMetric;
    this.missenseScoresService.getHistogramData("SSC", selectedMetric.id).subscribe(
      (histogramData) => {
        this.histogramData = histogramData;
    });
  }

  get selectedMetric() {
    return this.internalSelectedMetric;
  }
}
