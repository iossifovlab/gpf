import { Input, Component, ViewContainerRef, ComponentFactoryResolver, HostListener } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component'
import { ResizeService } from '../resize.service'

@Component({
    selector: 'gpf-table-view-empty-cell',
    template: ''
})
export class GpfTableEmptyCellComponent {
    @Input() columnInfo: GpfTableColumnComponent;
    private nativeElement: any;

    constructor(private viewContainer: ViewContainerRef, private resizeService: ResizeService) {
        this.nativeElement = viewContainer.element.nativeElement
    }

    ngOnInit() {
        this.resizeService.addResizeEventListener(this.nativeElement, (elem) => {
          this.recalcWidth()
        });
    }

    ngAfterViewInit() {
        this.recalcWidth()
    }

    recalcWidth() {
        let width = this.nativeElement.getBoundingClientRect().width
        if (width > 0 && width != this.columnInfo.width) {
            this.columnInfo.width = width
            console.log(this.columnInfo.width)
        }

    }
}
