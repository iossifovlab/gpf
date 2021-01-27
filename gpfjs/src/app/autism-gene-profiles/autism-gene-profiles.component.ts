import { AfterViewInit, Component, OnInit, ViewChild } from '@angular/core';
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { IDropdownSettings } from 'ng-multiselect-dropdown';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  @ViewChild(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu;
  private config$: Observable<AutismGeneToolConfig>;
  private genes$: Observable<AutismGeneToolGene[]>;

  private geneLists: string[];
  // private shownGeneListsCount: Number;
  // private geneListsCount: Number;
  // private collapseSymbol: String = String.fromCharCode(0x022B2);

  dropdownSettings: IDropdownSettings = {};

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.dropdownSettings = {
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true,
      defaultOpen: true,
      // itemsShowLimit: 3
    };

    this.config$ = this.autismGeneProfilesService.getConfig();
    this.config$.take(1).subscribe(res => {
      this.geneLists = res['geneLists'];
      // this.geneListsCount = res['geneLists'].length;
      // this.shownGeneListsCount = this.geneListsCount;
    });

    this.genes$ = this.autismGeneProfilesService.getGenes();

    this.config$.subscribe(res => {console.log(res); });
    this.genes$.subscribe(res => {console.log(res); });
  }

  calculateDatasetColspan(datasetConfig) {
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  // getShownGeneLists(geneLists) {
  //   return geneLists.slice(0, this.shownGeneListsCount);
  // }

  // showOrHideGeneLists() {
  //   if (this.shownGeneListsCount === this.geneListsCount) {
  //     this.shownGeneListsCount = 5;
  //     this.collapseSymbol = String.fromCharCode(0x022B3);
  //   } else {
  //     this.shownGeneListsCount = this.geneListsCount;
  //     this.collapseSymbol = String.fromCharCode(0x022B2);
  //   }
  // }

  sortAlphabetically(array: string[]): string[] {
    return array.sort((a, b) => {
      if (a < b) { return -1; }
      if (a > b) { return 1; }
      return 0;
   });
  }
}
