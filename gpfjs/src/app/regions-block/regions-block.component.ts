import { Component, OnInit } from '@angular/core';
import { REGIONS_BLOCK_TAB_DESELECT } from '../store/common';
import { Store } from '@ngrx/store';

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css']
})
export class RegionsBlockComponent implements OnInit {

  constructor(
    private store: Store<any>
  ) { }

  ngOnInit() {
  }

  onTabChange(event) {
    this.store.dispatch({
      'type': REGIONS_BLOCK_TAB_DESELECT,
      'payload': event.activeId
    });
    console.log(event);
  }

}
