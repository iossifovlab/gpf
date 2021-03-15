import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { AutismGeneToolConfig } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-table/autism-gene-profiles.service';

@Component({
  selector: 'gpf-autism-gene-profiles-block',
  templateUrl: './autism-gene-profiles-block.component.html',
  styleUrls: ['./autism-gene-profiles-block.component.css']
})
export class AutismGeneProfilesBlockComponent implements OnInit {
  @ViewChild('nav') nav: NgbNav;
  geneTabs = new Set<string>();
  autismGeneToolConfig: AutismGeneToolConfig;

  @HostListener('window:keydown', ['$event'])
  keyEvent($event: KeyboardEvent) {
    if ($event.target['localName'] === 'input') {
      return;
    }

    const key = $event.key;

    if (key === 'w') {
      this.closeActiveTab();
    } else if (
        Number(key)
        || key === '0'
        || key === 'p'
        || key === 'n'
      ) {
      this.openTabByKey($event.key);
    }
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.autismGeneProfilesService.getConfig().take(1).subscribe(config => {
      this.autismGeneToolConfig = config;
    });
  }

  createTabEventHandler($event): void {
    const tabId: string = $event.geneSymbol;
    const openTab: boolean = $event.openTab;

    this.geneTabs.add(tabId);
    if (openTab) {
      this.nav.select(tabId);
    }
  }

  getActiveTabIndex(): number {
    return [...this.geneTabs].indexOf(this.nav.activeId);
  }

  openHomeTab(): void {
    this.nav.select('autismGenesTool');
  }

  openPreviousTab(): void {
    const index = this.getActiveTabIndex();

    if (index > 0) {
      this.openTabAtIndex(index - 1);
    } else {
      this.openHomeTab();
    }
  }

  openNextTab(): void {
    const index = this.getActiveTabIndex();

    if (index + 1 < this.geneTabs.size) {
      this.openTabAtIndex(index + 1);
    }
  }

  openLastTab(): void {
    this.nav.select([...this.geneTabs][this.geneTabs.size - 1]);
  }

  openTabAtIndex(index: number): void {
    this.nav.select([...this.geneTabs][index]);
  }

  closeTab(event: MouseEvent, tabId: string): void {
    if (tabId === 'autismGenesTool') {
      return;
    }

    if (this.nav.activeId === tabId) {
      this.closeActiveTab();
    } else {
      this.geneTabs.delete(tabId);
    }

    event.preventDefault();
    event.stopImmediatePropagation();
  }

  closeActiveTab(): void {
    if (this.nav.activeId === 'autismGenesTool') {
      return;
    }

    const index = this.getActiveTabIndex();
    this.geneTabs.delete(this.nav.activeId);

    if ([...this.geneTabs].length === 0) {
      this.openHomeTab();
    } else if ([...this.geneTabs].length === index) {
      this.openLastTab();
    } else {
      this.openTabAtIndex(index);
    }
  }

  openTabByKey(key: string): void {
    if (this.geneTabs.size === 0) {
      return;
    }

    if (key === '0') {
      this.openLastTab();
    } else if (key === '1') {
      this.openHomeTab();
    } else if (Number(key) - 1 <= this.geneTabs.size) {
      this.openTabAtIndex(Number(key) - 2);
    } else if (key === 'p') {
      this.openPreviousTab();
    } else if (key === 'n') {
      this.openNextTab();
    }
  }
}
