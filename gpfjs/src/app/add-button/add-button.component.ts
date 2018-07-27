import { Component, OnInit, Input } from '@angular/core';

import { environment } from '../../environments/environment';

@Component({
  selector: 'gpf-add-button',
  templateUrl: './add-button.component.html',
  styleUrls: ['./add-button.component.css']
})
export class AddButtonComponent implements OnInit {
  @Input() addFilter: Function;

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  constructor() { }

  ngOnInit() {
  }

}
