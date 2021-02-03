import { Component, OnInit, ViewChildren } from '@angular/core';
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  @ViewChildren(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu[];

  private config$: Observable<AutismGeneToolConfig>;
  private genes$: Observable<AutismGeneToolGene[]>;

  private shownGeneLists: string[];
  private shownAutismScores: string[];
  private shownProtectionScores: string[];

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.config$ = this.autismGeneProfilesService.getConfig();
    this.config$.take(1).subscribe(res => {
      this.shownGeneLists = res['geneLists'];
      this.shownAutismScores = res['autismScores'];
      this.shownProtectionScores = res['protectionScores'];
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
}
