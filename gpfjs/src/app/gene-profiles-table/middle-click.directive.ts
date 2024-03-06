import { Directive, EventEmitter, HostListener, Output } from '@angular/core';

@Directive({
  selector: '[middleclick]'
})
export class MiddleClickDirective {
  @Output('middleclick') public middleClick = new EventEmitter();

  @HostListener('mouseup', ['$event'])
  public middleclickEvent(event: MouseEvent): void {
    if (event.which === 2) {
      this.middleClick.emit(event);
    }
  }
}
