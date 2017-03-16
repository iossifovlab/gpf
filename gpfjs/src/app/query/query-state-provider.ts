import { AfterContentInit, ContentChildren, QueryList, ViewChildren, forwardRef } from '@angular/core';

import { GeneSetsComponent } from '../gene-sets/gene-sets.component'
import { GenesBlockComponent } from '../genes-block/genes-block.component'
import { UsersComponent } from '../users/users.component'
import { GenderComponent } from '../gender/gender.component'


export class QueryStateProvider {
  getState() {
    return "AA";
  }
}


export class QueryStateCollector {
  @ViewChildren(forwardRef(() => QueryStateProvider)) directContentChildren: QueryList<QueryStateProvider>;
  @ViewChildren(forwardRef(() => QueryStateCollector)) contentChildren: QueryList<QueryStateCollector>;

  collectState() {
    let directState = this.directContentChildren.map((children) => children.getState());
    console.log("directState", directState);
    let indirectState = this.contentChildren.reduce((acc, current) => acc.concat(current.collectState()), []);
    console.log("indirectState", indirectState);

    return directState.concat(indirectState);
  }
}
