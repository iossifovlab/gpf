import { Component, OnInit, Input } from '@angular/core';

import { environment } from '../../environments/environment';

@Component({
  selector: 'gpf-remove-button',
  templateUrl: './remove-button.component.html',
  styleUrls: ['./remove-button.component.css']
})
export class RemoveButtonComponent implements OnInit {
  @Input() removeFilter: Function;
  @Input() field: any;

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  constructor() { }

  ngOnInit() {
  }

}
