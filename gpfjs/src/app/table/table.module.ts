import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent } from './table.component';

import { GpfTableColumnComponent } from './component/column.component';
import { GpfTableSubheaderComponent } from './component/subheader.component';
import { GpfTableContentHeaderComponent } from './component/header.component';
import { GpfTableCellContentDirective } from './component/content.directive';
import { GpfTableCellContentComponent } from './component/cell.component';
import { GpfTableLegendDirective } from './component/legend.directive';

import { GpfTableHeaderCellComponent } from './view/header/header-cell.component';
import { GpfTableHeaderComponent } from './view/header/header.component';
import { GpfTableCellComponent } from './view/cell.component';

@NgModule({
  declarations: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubheaderComponent,
    GpfTableContentHeaderComponent,
    GpfTableCellContentDirective,
    GpfTableHeaderCellComponent,
    GpfTableHeaderComponent,
    GpfTableCellComponent,
    GpfTableLegendDirective,
    GpfTableCellContentComponent
  ],
  exports: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubheaderComponent,
    GpfTableContentHeaderComponent,
    GpfTableCellContentDirective,
    GpfTableLegendDirective,
    GpfTableCellContentComponent
  ],
  imports: [CommonModule]
})
export class GpfTableModule { }
