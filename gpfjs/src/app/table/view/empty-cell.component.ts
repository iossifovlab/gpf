import { Input, Component, ViewContainerRef, AfterViewInit } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component';
import { ResizeService } from '../resize.service';

@Component({
  selector: 'gpf-table-view-empty-cell',
  template: '',
  standalone: false
})
export class GpfTableEmptyCellComponent implements AfterViewInit {
  @Input() public columnInfo: GpfTableColumnComponent;
  private nativeElement: any;
  private firstRecalc = true;
  private isCustomWidth = false;

  public constructor(
    private viewContainer: ViewContainerRef,
    private resizeService: ResizeService
  ) {
    this.nativeElement = viewContainer.element.nativeElement;
  }

  public ngAfterViewInit(): void {
    this.resizeService.addResizeEventListener(this.nativeElement, () => {
      this.recalcWidth();
    });
    setTimeout(() => {
      this.recalcWidth();
    });
  }

  private recalcWidth(): void {
    if (this.firstRecalc) {
      this.firstRecalc = false;
      this.isCustomWidth = this.columnInfo.columnWidth !== '';
    }

    if (this.isCustomWidth) {
      return;
    }

    const width = this.nativeElement.getBoundingClientRect().width;
    if (width > 0 && width !== this.columnInfo.columnWidth) {
      this.columnInfo.columnWidth = width + 'px';
    }
  }
}
