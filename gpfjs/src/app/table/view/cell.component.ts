import { Input, Component, ViewContainerRef, ComponentFactoryResolver, HostListener } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component'
import { ResizeService } from '../resize.service'

@Component({
    selector: 'gpf-table-view-cell',
    templateUrl: './cell.component.html'
})
export class GpfTableCellComponent {
    @Input() columnInfo: GpfTableColumnComponent;
    @Input() data: any;

    constructor() {
    }

    get cellContent() {
        return this.columnInfo.contentChildren.first
    }
}
