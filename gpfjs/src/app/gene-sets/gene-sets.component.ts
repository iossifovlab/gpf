import { Component } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css']
})
export class GeneSetsComponent {
  private geneSetsCollections: Array<GeneSetsCollection>;
  private geneSets: Array<GeneSet>;
  private internalSelectedGeneSet: any;
  private selectedGeneSet: GeneSet;
  private searchQuery: string;

  constructor(
    private geneSetsService: GeneSetsService,
  )  { }

  ngOnInit() {
    this.geneSetsService.getGeneSetsCollections().subscribe(
      (geneSetsCollections) => {
        this.geneSetsCollections = geneSetsCollections;
    });
  }

  onSearch(searchTerm) {
    this.searchQuery = searchTerm;
    this.geneSetsService.getGeneSets(this.selectedGeneSetsCollection.name, searchTerm).subscribe(
      (geneSets) => {
        this.geneSets = geneSets.sort((a, b) => a.name.localeCompare(b.name));
    });
  }

  onSelect(event) {
    this.selectedGeneSet = event;
  }

  get selectedGeneSetsCollection(): any {
    return this.internalSelectedGeneSet;
  }

  set selectedGeneSetsCollection(selectedGeneSet: any) {
    this.internalSelectedGeneSet = selectedGeneSet;
    this.selectedGeneSet = null;
    this.geneSets = null;
    this.onSearch("");
  }
}
