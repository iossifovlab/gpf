import { Component, EventEmitter, Input, OnChanges, OnInit, Output, ViewChildren } from '@angular/core';
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit, OnChanges {
  @Input() config: AutismGeneToolConfig;
  @Output() createTabEvent = new EventEmitter();
  @ViewChildren(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu[];

  private genes$: Observable<AutismGeneToolGene[]>;

  private shownGeneLists: string[];
  private shownAutismScores: string[];
  private shownProtectionScores: string[];

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnChanges(): void {
    if (this.config) {
      this.shownGeneLists = this.config['geneLists'];
      this.shownAutismScores = this.config['autismScores'];
      this.shownProtectionScores = this.config['protectionScores'];
    }
  }

  ngOnInit(): void {
    this.genes$ = this.autismGeneProfilesService.getGenes();
  }

  calculateDatasetColspan(datasetConfig) {
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  sortAlphabetically(array: string[]): string[] {
    return array.sort((a, b) => {
      if (a < b) { return -1; }
      if (a > b) { return 1; }
      return 0;
   });
  }

  handleMultipleSelectMenuApplyEvent($event) {
    if ($event.id === 'geneLists') {
      this.shownGeneLists = $event.data;
    } else if ($event.id === 'autismScores') {
      this.shownAutismScores = $event.data;
    } else if ($event.id === 'protectionScores') {
      this.shownProtectionScores = $event.data;
    }

    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  emitCreateTabEvent(geneSymbol: string, openTab: boolean): void {
    this.createTabEvent.emit({geneSymbol: geneSymbol, openTab: openTab});
  }
}
