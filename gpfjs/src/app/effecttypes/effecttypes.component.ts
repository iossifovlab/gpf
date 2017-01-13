import { Component, OnInit } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { IdDescription } from '../common/iddescription';

@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css']
})
export class EffecttypesComponent implements OnInit {

  private selectedDatasetId: string;
  buttonGroups: IdDescription[];
  columnGroups: IdDescription[];

  private effectTypesColumns: Map<string, string[]>;
  private effectTypesButtons: Map<string, string[]>;
  private selectedEffectTypes = new Set<string>();

  constructor(
    private datasetService: DatasetService
  ) { }

  ngOnInit() {
    this.selectedDatasetId = this.datasetService.selectedDatasetId;
    this.initButtonGroups();
    this.initColumnGroups();
  }

  private initButtonGroups(): void {
    this.datasetService.getEffecttypesGroupsButtons(this.selectedDatasetId)
      .then(buttons => {
        this.buttonGroups = buttons;
        this.effectTypesButtons = new Map<string, string[]>();
        for (let group of this.buttonGroups) {
          this.datasetService.getEffecttypesInGroup(group.id)
            .then(effecttypes => {
              this.effectTypesButtons.set(group.id, effecttypes);
            });
        }
      });
  }

  private initColumnGroups(): void {
    this.datasetService.getEffecttypesGroupsColumns(this.selectedDatasetId)
      .then(columns => {
        this.columnGroups = columns;
        this.effectTypesColumns = new Map<string, string[]>();
        for (let group of this.columnGroups) {
          this.datasetService.getEffecttypesInGroup(group.id)
            .then(effecttypes => {
              this.effectTypesColumns.set(group.id, effecttypes);
            });
        }
      });
  }

  selectButtonGroup(groupId: string): void {

  }
  selectAll(): void {

  }

  selectNone(): void {

  }

  selectLgds(): void {

  }

  selectNonsynonymous(): void {

  }

  selectUtrs(): void {

  }
}
