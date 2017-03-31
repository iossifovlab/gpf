import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css']
})
export class CategoricalFilterComponent implements OnInit {
  @Input() name: string;
  @Input() domain: Array<string>;

  constructor() { }

  ngOnInit() {
  }

}
