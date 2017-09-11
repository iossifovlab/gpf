import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent,
         GpfTableColumnComponent,
         GpfTableCellComponent,
         GpfTableSubcolumnComponent,
         GpfTableCellHeaderDirective,
         GpfTableCellContentDirective,
         GpfTableLegendDirective } from './table.component';
import { GpfTableHeaderCellComponent } from './header/table-header-cell.component';

@NgModule({
  declarations: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubcolumnComponent,
    GpfTableCellContentDirective,
    GpfTableCellHeaderDirective,
    GpfTableHeaderCellComponent,
    GpfTableCellComponent,
    GpfTableLegendDirective
  ],
  exports: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubcolumnComponent,
    GpfTableCellContentDirective,
    GpfTableCellHeaderDirective,
    GpfTableLegendDirective
  ],
  imports: [CommonModule]
})
export class GpfTableModule { }
