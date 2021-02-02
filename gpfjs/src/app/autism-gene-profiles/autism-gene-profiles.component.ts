import { Component, OnInit, ViewChild } from '@angular/core';
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  @ViewChild(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild(MultipleSelectMenuComponent) multipleSelectMenuComponent;

  private config$: Observable<AutismGeneToolConfig>;
  private genes$: Observable<AutismGeneToolGene[]>;

  private shownGeneLists: string[];

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.config$ = this.autismGeneProfilesService.getConfig();
    this.config$.take(1).subscribe(res => {
      this.shownGeneLists = res['geneLists'];
    });

    this.genes$ = this.autismGeneProfilesService.getGenes();

    this.config$.subscribe(res => {console.log(res); });
    this.genes$.subscribe(res => {console.log(res); });
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

  handleMultipleSelectMenuApplyEvent($event: string[]) {
    this.setShownGeneLists($event);
    this.ngbDropdownMenu.dropdown.close();
  }

  setShownGeneLists(geneLists: string[]) {
    this.shownGeneLists = geneLists;
  }

  emitApplyEventOnMultipleSelectMenuCloseEvent(isOpen: boolean) {
    if (!isOpen) {
      this.multipleSelectMenuComponent.apply();
    }
  }
}
