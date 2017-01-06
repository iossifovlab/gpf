import { Component, OnInit } from '@angular/core';
import { IdDescription } from '../common/iddescription';
import { DatasetService } from '../dataset/dataset.service';

@Component({
  selector: 'gpf-studytypes',
  templateUrl: './studytypes.component.html',
  styleUrls: ['./studytypes.component.css']
})
export class StudytypesComponent implements OnInit {

  studytypes: IdDescription[];
  studytypesCheck: boolean[];

  constructor(
    private datasetService: DatasetService
  ) { }

  ngOnInit() {
    this.datasetService.getStudytypes(this.datasetService.selectedDatasetId)
      .then(studytypes => {
        this.studytypes = studytypes;
        this.studytypesCheck = new Array<boolean>(this.studytypes.length);
        this.selectAll();
      });
  }


  selectAll(): void {
    if (this.studytypes) {
      for (let i = 0; i < this.studytypesCheck.length; i++) {
        this.studytypesCheck[i] = true;
      }
    }
  }

  selectNone(): void {
    if (this.studytypes) {
      for (let i = 0; i < this.studytypesCheck.length; i++) {
        this.studytypesCheck[i] = false;
      }
    }
  }

  getSelectedPhenotypes(): Set<string> {
    let selectedPhenotypes: Set<string> = new Set<string>();
    if (this.studytypes) {
      for (let i = 0; i < this.studytypesCheck.length; i++) {
        if (this.studytypesCheck[i]) {
          selectedPhenotypes.add(this.studytypes[i].id);
        }
      }
    }
    return selectedPhenotypes;
  }
}
