import { Component } from '@angular/core';
import { NgbTabset } from  '@ng-bootstrap/ng-bootstrap';


@Component({
  selector: 'gpf-tabset',
  host: {'role': 'tabpanel'},
  templateUrl: './tabset.component.html',
})
export class GpfTabsetComponent extends NgbTabset {
}
