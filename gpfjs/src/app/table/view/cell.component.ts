import { Input, Component } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component';

@Component({
    selector: 'gpf-table-view-cell',
    templateUrl: './cell.component.html',
    styleUrls: ['./cell.component.css'],
})
export class GpfTableCellComponent {
    @Input() columnInfo: GpfTableColumnComponent;
    @Input() data: any;
    @Input() noScrollOptimization: boolean;

    constructor() {
    }

    get cellContent() {
        return this.columnInfo.contentChildren.first;
    }
}
