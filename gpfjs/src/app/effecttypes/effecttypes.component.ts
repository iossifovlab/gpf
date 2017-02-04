import { Component, OnInit, Input } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { IdName } from '../common/idname';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import {
  CODING,
  NONCODING,
  CNV, ALL, LGDS, NONSYNONYMOUS, UTRS,
} from './effecttypes';


@Component({
  selector: 'gpf-effecttypes-column',
  template: `
      <em>{{columnName}}</em>
      <div *ngFor="let effect of effectTypesLabels; let i=index" class="checkbox">
        <label><input type="checkbox" [checked]="effectTypesValues[i]">{{effect}}</label>
      </div>
  `
})
export class EffecttypesColumnComponent implements OnInit {
  @Input() effectTypes: Observable<string[]>;
  @Input() columnName: string;
  @Input() effectTypesLabels: string[];

  effectTypesValues: boolean[];

  ngOnInit() {
    this.effectTypesValues = new Array<boolean>(this.effectTypesLabels.length);
    for (let i = 0; i < this.effectTypesValues.length; ++i) {
      this.effectTypesValues[i] = false;
    }

    this.effectTypes.subscribe(values => {
      for (let i = 0; i < this.effectTypesLabels.length; ++i) {
        if (values.indexOf(this.effectTypesLabels[i]) !== -1) {
          this.effectTypesValues[i] = true;
        } else {
          this.effectTypesValues[i] = false;
        }
      }

    });
  }
};

@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css']
})
export class EffecttypesComponent implements OnInit {

  buttonGroups: IdName[];
  columnGroups: IdName[];

  effectTypesColumns: Map<string, string[]>;

  private effectTypesButtons: Map<string, string[]>;
  private selectedEffectTypes = new Map<string, boolean>();

  effectTypes: Observable<Array<string>>;

  constructor(
    private datasetService: DatasetService,
    private store: Store<any>
  ) {

    this.effectTypes = this.store.select('effectTypes');
    console.log(this.effectTypes);

    this.initButtonGroups();
    this.initColumnGroups();
  }

  ngOnInit() {
    this.selectButtonGroup('LGDS');
  }

  private initButtonGroups(): void {
    this.effectTypesButtons = new Map<string, string[]>();

    this.effectTypesButtons.set('ALL', ALL);
    this.effectTypesButtons.set('NONE', []);
    this.effectTypesButtons.set('LGDS', LGDS);
    this.effectTypesButtons.set('NONSYNONYMOUS', NONSYNONYMOUS);
    this.effectTypesButtons.set('UTRS', UTRS);

    this.buttonGroups = [
      { id: 'ALL', name: 'All' },
      { id: 'NONE', name: 'None' },
      { id: 'LGDS', name: 'LGDs' },
      { id: 'NONSYNONYMOUS', name: 'Nonsynonymous' },
      { id: 'UTRS', name: 'UTRs' },
    ];
  }

  private initColumnGroups(): void {
    this.effectTypesColumns = new Map<string, string[]>();

    this.effectTypesColumns.set('CODING', CODING);
    this.effectTypesColumns.set('NONCODING', NONCODING);
    this.effectTypesColumns.set('CNV', CNV);

    this.columnGroups = [
      { id: 'CODING', name: 'Coding' },
      { id: 'NONCODING', name: 'Noncoding' },
      { id: 'CNV', name: 'CNV' },
    ];

  }

  selectButtonGroup(groupId: string): void {

  }

}
