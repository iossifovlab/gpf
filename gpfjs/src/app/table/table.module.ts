import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent,
         GpfTableColumnComponent,
         GpfTableCell,
         GpfTableSubcolumnComponent,
         GpfTableCellHeaderDirective,
         GpfTableCellContentDirective,
         GpfTableHeader,
         GpfTableLegendDirective } from './table.component';

@NgModule({
  declarations: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubcolumnComponent,
    GpfTableCellContentDirective,
    GpfTableCellHeaderDirective,
    GpfTableHeader,
    GpfTableCell,
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
