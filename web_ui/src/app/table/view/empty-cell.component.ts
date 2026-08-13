import { Input, Component, ViewContainerRef, AfterViewInit, inject } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component';
import { ResizeService } from '../resize.service';

@Component({
  selector: 'gpf-table-view-empty-cell',
  template: '',
  standalone: false
})
export class GpfTableEmptyCellComponent implements AfterViewInit {
  private viewContainer = inject(ViewContainerRef);
  private resizeService = inject(ResizeService);

  @Input() public columnInfo: GpfTableColumnComponent;
  private nativeElement: HTMLElement;
  private firstRecalc = true;
  private isCustomWidth = false;

  public constructor() {
    const viewContainer = this.viewContainer;

    // ViewContainerRef.element is ElementRef<any>; this component's host is a DOM element.
    this.nativeElement = viewContainer.element.nativeElement as HTMLElement;
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
    // columnWidth is a CSS length, so compare the formatted value - comparing
    // the raw number against it was always unequal and re-assigned every tick.
    const columnWidth = `${width}px`;
    if (width > 0 && columnWidth !== this.columnInfo.columnWidth) {
      this.columnInfo.columnWidth = columnWidth;
    }
  }
}
