import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent,
         GpfTableColumnComponent,
         GpfTableCellComponent,
         GpfTableSubcolumnComponent,
         GpfTableCellHeaderDirective,
         GpfTableCellContentDirective,
         GpfTableHeaderComponent,
         GpfTableLegendDirective } from './table.component';

@NgModule({
  declarations: [
    GpfTableComponent,
    GpfTableColumnComponent,
    GpfTableSubcolumnComponent,
    GpfTableCellContentDirective,
    GpfTableCellHeaderDirective,
    GpfTableHeaderComponent,
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
