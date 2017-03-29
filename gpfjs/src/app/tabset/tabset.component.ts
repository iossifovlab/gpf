import { Component, ViewChild, ViewContainerRef } from '@angular/core';
import { NgbTabset, NgbTab } from  '@ng-bootstrap/ng-bootstrap';


@Component({
  selector: 'gpf-tabset',
  host: {'role': 'tabpanel'},
  templateUrl: './tabset.component.html',
})
export class GpfTabsetComponent extends NgbTabset {
  @ViewChild('ngTemplateOutletContainer', { read: ViewContainerRef })
  ngTemplateOutletContainer: ViewContainerRef;

  getTabById(id: string): NgbTab {
    let tabsWithId: NgbTab[] = this.tabs.filter(tab => tab.id === id);
    return tabsWithId.length ? tabsWithId[0] : null;
  }

  select(tabId: string) {
    let selectedTab = this.getTabById(tabId);
    if (selectedTab && !selectedTab.disabled && this.activeId !== selectedTab.id) {
      let defaultPrevented = false;

      if(this.ngTemplateOutletContainer) {
        this.ngTemplateOutletContainer.clear();
      }

      this.tabChange.emit(
          {activeId: this.activeId, nextId: selectedTab.id, preventDefault: () => { defaultPrevented = true; }});

      if (!defaultPrevented) {
        this.activeId = selectedTab.id;
      }
    }
  }

}
