import { Component, OnInit, Input } from '@angular/core';
import { GENES_BLOCK_TAB_DESELECT } from '../store/common';
import { Store } from '@ngrx/store';

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css']
})
export class GenesBlockComponent implements OnInit {
  @Input() showAllTab = true;

  constructor(
    private store: Store<any>
  ) { }

  ngOnInit() {
    this.store.dispatch({
      'type': GENES_BLOCK_TAB_DESELECT,
      'payload': null
    });
  }

  onTabChange(event) {
    this.store.dispatch({
      'type': GENES_BLOCK_TAB_DESELECT,
      'payload': event.activeId
    });
  }
}
