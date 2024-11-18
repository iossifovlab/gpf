import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HistogramComponent } from './histogram.component';
import { HistogramRangeSelectorLineComponent } from './histogram-range-selector-line.component';
import { FormsModule } from '@angular/forms';

@NgModule({
  declarations: [
    HistogramComponent,
    HistogramRangeSelectorLineComponent,
  ],
  exports: [
    HistogramComponent,
    HistogramRangeSelectorLineComponent
  ],
  imports: [
    CommonModule,
    FormsModule
  ]
})
export class HistogramModule { }
