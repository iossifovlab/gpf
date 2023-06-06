import { Input, ContentChildren, QueryList, Component, OnInit } from '@angular/core';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableContentComponent } from './content.component';

@Component({
  selector: 'gpf-table-column',
  template: '',
})
export class GpfTableColumnComponent implements OnInit {
  @ContentChildren(GpfTableContentHeaderComponent) public headerChildren: QueryList<GpfTableContentHeaderComponent>;
  @ContentChildren(GpfTableContentComponent) public contentChildren: QueryList<GpfTableContentComponent>;
  @Input() public columnWidth = '';
  @Input() public columnMaxWidth = '';

  public ngOnInit(): void {
    if (this.columnWidth.endsWith('%')) {
      const percentage = Number(this.columnWidth.slice(0, -1));
      this.updateColumnWidth(percentage);
      window.addEventListener('resize', () => {
        this.updateColumnWidth(percentage);
      });
    }
  }

  private updateColumnWidth(percentage): void {
    const browserWidth = window.innerWidth;
    const pixelWidth = browserWidth * percentage / 100;
    this.columnWidth = String(pixelWidth) + 'px';
  }
}
