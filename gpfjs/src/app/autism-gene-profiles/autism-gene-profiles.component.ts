import { AfterViewInit, Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  private config$: Observable<AutismGeneToolConfig>;
  private genes$: Observable<AutismGeneToolGene[]>;
  private shownGeneListsCount: Number;
  private geneListsCount: Number;

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.config$ = this.autismGeneProfilesService.getConfig();
    this.config$.take(1).subscribe(res => {
      this.geneListsCount = res['geneLists'].length;
      this.shownGeneListsCount = this.geneListsCount;
    });

    this.genes$ = this.autismGeneProfilesService.getGenes();

    this.config$.subscribe(res => {console.log(res); });
    this.genes$.subscribe(res => {console.log(res); });
  }

  calculateDatasetColspan(datasetConfig) {
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  getShownGeneLists(geneLists) {
    return geneLists.slice(0, this.shownGeneListsCount);
  }

  showOrHideGeneLists() {
    if (this.shownGeneListsCount === this.geneListsCount) {
      this.shownGeneListsCount = 5;
    } else {
      this.shownGeneListsCount = this.geneListsCount;
    }
  }
}
