import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-autism-gene-profiles-block',
  templateUrl: './autism-gene-profiles-block.component.html',
  styleUrls: ['./autism-gene-profiles-block.component.css']
})
export class AutismGeneProfilesBlockComponent implements OnInit {
  private geneTabs = new Set<string>();

  constructor() { }

  ngOnInit(): void {
  }

  openTabEventHandler($event) {
    this.geneTabs.add($event);
  }

  close(event: MouseEvent, toRemove: string) {
    this.geneTabs.delete(toRemove);
    event.preventDefault();
    event.stopImmediatePropagation();
  }
}
