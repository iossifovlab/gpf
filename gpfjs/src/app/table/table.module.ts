import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent } from './table.component';
import { ResizeService } from './resize.service'

import { GpfTableColumnComponent } from './component/column.component';
import { GpfTableSubheaderComponent } from './component/subheader.component';
import { GpfTableContentHeaderComponent } from './component/header.component';
import { GpfTableCellContentDirective } from './component/content.directive';
import { GpfTableContentComponent } from './component/content.component';
import { GpfTableSubcontentComponent } from './component/subcontent.component';
import { GpfTableLegendDirective } from './component/legend.directive';

import { GpfTableHeaderCellComponent } from './view/header/header-cell.component';
import { GpfTableHeaderComponent } from './view/header/header.component';
import { GpfTableCellComponent } from './view/cell.component';
import { GpfTableEmptyCellComponent } from './view/empty-cell.component';

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
    GpfTableContentComponent,
    GpfTableSubcontentComponent,
    GpfTableEmptyCellComponent
  ],
  providers: [
      ResizeService
  ],
  exports: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubheaderComponent,
    GpfTableContentHeaderComponent,
    GpfTableCellContentDirective,
    GpfTableLegendDirective,
    GpfTableContentComponent,
    GpfTableSubcontentComponent
  ],
  imports: [CommonModule]
})
export class GpfTableModule { }
