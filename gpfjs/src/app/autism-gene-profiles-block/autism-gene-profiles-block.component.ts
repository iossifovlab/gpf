import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-autism-gene-profiles-block',
  templateUrl: './autism-gene-profiles-block.component.html',
  styleUrls: ['./autism-gene-profiles-block.component.css']
})
export class AutismGeneProfilesBlockComponent implements OnInit {
  private geneTabs: string[] = [];

  constructor() { }

  ngOnInit(): void {
  }

  newTab() {
    this.geneTabs.push('CHD8');
  }

  close(event: MouseEvent, toRemove: string) {
    this.geneTabs = this.geneTabs.filter(geneTab => geneTab !== toRemove);
    event.preventDefault();
    event.stopImmediatePropagation();
  }
}
