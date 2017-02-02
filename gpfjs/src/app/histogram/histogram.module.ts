import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { HistogramComponent } from './histogram.component';
import { HistogramRangeSelectorLineComponent } from './histogram-range-selector-line.component';

@NgModule({
  declarations: [
    HistogramComponent,
    HistogramRangeSelectorLineComponent,
  ],
  exports: [
    HistogramComponent,
  ],
  imports: [CommonModule]
})
export class HistogramModule { }
