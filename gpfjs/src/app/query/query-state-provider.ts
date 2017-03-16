import { AfterContentInit, ContentChildren, QueryList, ViewChildren, forwardRef } from '@angular/core';

import { GeneSetsComponent } from '../gene-sets/gene-sets.component'
import { GenesBlockComponent } from '../genes-block/genes-block.component'
import { UsersComponent } from '../users/users.component'
import { GenderComponent } from '../gender/gender.component'


export class QueryStateProvider {
  getState() {
    return null;
  }
}


export class QueryStateCollector {
  @ViewChildren(forwardRef(() => QueryStateProvider)) directContentChildren: QueryList<QueryStateProvider>;
  @ViewChildren(forwardRef(() => QueryStateCollector)) contentChildren: QueryList<QueryStateCollector>;

  collectState() {
    let directState = this.directContentChildren.map((children) => children.getState());
    let indirectState = this.contentChildren.reduce((acc, current) => acc.concat(current.collectState()), []);
    return directState.concat(indirectState);
  }
}
