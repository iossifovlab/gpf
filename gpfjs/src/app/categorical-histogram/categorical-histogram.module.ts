import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { FormsModule } from '@angular/forms';
import { HistogramModule } from 'app/histogram/histogram.module';
import { CategoricalHistogramComponent } from './categorical-histogram.component';

@NgModule({
  declarations: [
    CategoricalHistogramComponent,
  ],
  exports: [
    CategoricalHistogramComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    HistogramModule
  ]
})
export class CategoricalHistogramModule { }