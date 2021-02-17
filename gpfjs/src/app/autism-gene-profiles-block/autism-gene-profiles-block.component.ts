import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { AutismGeneToolConfig } from 'app/autism-gene-profiles/autism-gene-profile';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles/autism-gene-profiles.service';

@Component({
  selector: 'gpf-autism-gene-profiles-block',
  templateUrl: './autism-gene-profiles-block.component.html',
  styleUrls: ['./autism-gene-profiles-block.component.css']
})
export class AutismGeneProfilesBlockComponent implements OnInit {
  @ViewChild('nav') nav: NgbNav;
  private geneTabs = new Set<string>();
  private autismGeneToolConfig: AutismGeneToolConfig;

  @HostListener('window:keydown', ['$event'])
  keyEvent($event: KeyboardEvent) {
    if ($event.key === 'w') {
      this.closeActiveTab();
    }

    if (Number($event.key) || $event.key === '0' || $event.key === '`') {
      this.openTabByKey($event.key);
    }

    if ($event.key === 'a' || $event.key === 'q' || $event.key === 'ArrowLeft') {
      this.openPreviousTab();
    }

    if ($event.key === 'd' || $event.key === 'e' || $event.key === 'ArrowRight') {
      this.openNextTab();
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

  createTabEventHandler($event) {
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

  openHomeTab() {
    this.nav.select('autismGenesTool');
  }

  openPreviousTab() {
    const index = this.getActiveTabIndex();

    if (index > 0) {
      this.openTabAtIndex(index - 1);
    } else {
      this.openHomeTab();
    }
  }

  openNextTab() {
    const index = this.getActiveTabIndex();

    if (index + 1 < this.geneTabs.size) {
      this.openTabAtIndex(index + 1);
    }
  }

  openLastTab() {
    this.nav.select([...this.geneTabs][this.geneTabs.size - 1]);
  }

  openTabAtIndex(index: number) {
    this.nav.select([...this.geneTabs][index]);
  }

  closeTab(event: MouseEvent, tabId: string) {
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

  closeActiveTab() {
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

  openTabByKey(key) {
    if (this.geneTabs.size === 0) {
      return;
    }

    if (key === '0' || key === '9') {
      this.openLastTab();
    } else if (key === '1' || key === '`') {
      this.openHomeTab();
    } else if (Number(key) - 1 <= this.geneTabs.size) {
      this.openTabAtIndex(Number(key) - 2);
    }
  }
}
