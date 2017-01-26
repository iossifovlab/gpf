import { NgModule } from '@angular/core';
import { CommonModule }        from '@angular/common';

import { GpfTableComponent, 
         GpfCustomTemplateComponent, 
         GpfTableColumnComponent, 
         GpfTableCell, 
         GpfTableSubcolumnComponent, 
         GpfTableCellHeaderDirective, 
         GpfTableCellContentDirective, 
         GpfTableHeader } from './table.component';

@NgModule({
  declarations: [
    GpfTableComponent,
    GpfTableColumnComponent, 
    GpfTableSubcolumnComponent,
    GpfTableCellContentDirective,
    GpfTableCellHeaderDirective,
    GpfTableHeader,
    GpfCustomTemplateComponent,
    GpfTableCell
  ],
  exports: [
    GpfTableComponent, 
    GpfTableColumnComponent, 
    GpfTableSubcolumnComponent, 
    GpfTableCellContentDirective, 
    GpfTableCellHeaderDirective
  ],
  imports: [CommonModule]
})
export class GpfTableModule { }

