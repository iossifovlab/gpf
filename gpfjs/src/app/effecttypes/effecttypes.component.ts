import { Component, OnInit } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';


@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css']
})
export class EffecttypesComponent implements OnInit {

  private readonly ALL: string[] = [
    'Nonsense',
    'Frame-shift',
    'Splice-site',
    'Missense',
    'Non-frame-shift',
    'noStart',
    'noEnd',
    'Synonymous',
    'Non coding',
    'Intron',
    'Intergenic',
    '3\'-UTR',
    '5\'-UTR',
    'CNV+',
    'CNV-'
  ];

  private readonly CODING: string[] = [
    'Nonsense',
    'Frame-shift',
    'Splice-site',
    'Missense',
    'Non-frame-shift',
    'noStart',
    'noEnd',
    'Synonymous',
  ];

  private readonly NONCODING: string[] = [
    'Non coding',
    'Intron',
    'Intergenic',
    '3\'-UTR',
    '5\'-UTR',
  ];

  private readonly CNV: string[] = [
    'CNV+',
    'CNV-'
  ];

  private readonly LGDS: string[] = [
    'Nonsense',
    'Frame-shift',
    'Splice-site',
  ];

  private readonly NONSYNONYMOUS: string[] = [
    'Nonsense',
    'Frame-shift',
    'Splice-site',
    'Missense',
    'Non-frame-shift',
    'noStart',
    'noEnd',
  ];

  private readonly UTRS: string[] = [
    '3\'-UTR',
    '5\'-UTR',
  ];

  private selectedDatasetId: string;
  buttonGroups: IdName[];
  columnGroups: IdName[];

  effectTypesColumns: Map<string, string[]>;

  private effectTypesButtons: Map<string, string[]>;
  private selectedEffectTypes = new Map<string, boolean>();

  constructor(
    private datasetService: DatasetService
  ) {

    for (let effectTypes of [this.CODING, this.NONCODING, this.CNV]) {
      for (let effectType of effectTypes) {
        this.selectedEffectTypes.set(effectType, false);
      }
    }
    this.initButtonGroups();
    this.initColumnGroups();
  }

  ngOnInit() {
    this.selectButtonGroup('LGDS');
  }

  private initButtonGroups(): void {
    this.effectTypesButtons = new Map<string, string[]>();

    this.effectTypesButtons.set('ALL', this.ALL);
    this.effectTypesButtons.set('NONE', []);
    this.effectTypesButtons.set('LGDS', this.LGDS);
    this.effectTypesButtons.set('NONSYNONYMOUS', this.NONSYNONYMOUS);
    this.effectTypesButtons.set('UTRS', this.UTRS);

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

    this.effectTypesColumns.set('CODING', this.CODING);
    this.effectTypesColumns.set('NONCODING', this.NONCODING);
    this.effectTypesColumns.set('CNV', this.CNV);

    this.columnGroups = [
      { id: 'CODING', name: 'Coding' },
      { id: 'NONCODING', name: 'Noncoding' },
      { id: 'CNV', name: 'CNV' },
    ];

  }

  private deselectAll(): void {
    this.selectedEffectTypes.forEach((value: boolean, key: string) => {
      this.selectedEffectTypes.set(key, value);
    });
  }

  selectButtonGroup(groupId: string): void {

  }

}
