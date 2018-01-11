import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-errors-alert',
  templateUrl: './errors-alert.component.html',
  styleUrls: ['./errors-alert.component.css']
})
export class ErrorsAlertComponent implements OnInit {
  @Input()
  errors: Array<string>;

  constructor() { }

  ngOnInit() {
  }

}
