import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent,
         GpfTableColumnComponent,
         GpfTableCellComponent,
         GpfTableSubheaderComponent,
         GpfTableContentHeaderComponent,
         GpfTableCellContentDirective,
         GpfTableCellContentComponent,
         GpfTableLegendDirective } from './table.component';
import { GpfTableHeaderCellComponent } from './header/table-header-cell.component';
import { GpfTableHeaderComponent } from './header/table-header.component';

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
