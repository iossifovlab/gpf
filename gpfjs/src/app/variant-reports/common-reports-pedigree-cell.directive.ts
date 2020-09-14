import { Directive, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[gpfPedigreeHost]'
})
export class CommonReportsPedigreeCellDirective {

  constructor(public viewContainerRef: ViewContainerRef) { }

}
