import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { PedigreeChartComponent} from './pedigree-chart.component';
import { PedigreeChartMemberComponent } from './pedigree-chart-member.component';

@NgModule({
  declarations: [
    PedigreeChartComponent,
    PedigreeChartMemberComponent,
  ],
  exports: [
    PedigreeChartComponent,
  ],
  imports: [CommonModule]
})
export class PedigreeChartModule { }
