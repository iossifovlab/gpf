import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { QueryService } from 'app/query/query.service';
import { RouterTestingModule } from '@angular/router/testing';
import { GeneProfilesBlockComponent } from './gene-profiles-block.component';
import { GeneProfilesTableComponent } from 'app/gene-profiles-table/gene-profiles-table.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { NgxsModule } from '@ngxs/store';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { FormsModule } from '@angular/forms';
import { APP_BASE_HREF } from '@angular/common';
import { GeneProfilesService } from './gene-profiles.service';
import { Observable, of } from 'rxjs';
import { GeneProfilesSingleViewConfig } from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { TruncatePipe } from '../utils/truncate.pipe';
import { GeneProfilesColumn, GeneProfilesTableConfig } from 'app/gene-profiles-table/gene-profiles-table';
import { GeneProfilesState } from 'app/gene-profiles-table/gene-profiles-table.state';

const config = {
  geneLinkTemplates: [
    {
      name: 'link1',
      url: 'url1'
    },
    {
      name: 'link2',
      url: 'url2'
    }
  ],
  shown: [],
  defaultDataset: 'mockDataset',
  description: 'mock description',
  geneSets: [
    {
      category: 'autism_gene_sets',
      displayName: 'Autism Gene Sets',
      defaultVisible: true,
      sets: [
        { setId: 'SFARI ALL', defaultVisible: true, collectionId: 'sfari', meta: null }
      ]
    }
  ],
  genomicScores: [
    {
      category: 'autism_scores',
      defaultVisible: true,
      displayName: 'Autism Scores',
      scores: [
        { format: '%s', defaultVisible: true, scoreName: 'SFARI gene score', meta: null }
      ]
    }
  ],
  datasets: [
    {
      defaultVisible: true,
      displayName: 'Sequencing de Novo',
      id: 'sequencing_de_novo',
      meta: null,
      shown: [],
      personSets: [
        {
          id: 'autism',
          shown: [],
          defaultVisible: true,
          displayName: 'autism',
          collectionId: 'phenotype',
          description: '',
          parentsCount: 9836,
          childrenCount: 21775,
          statistics: [
            {
              id: 'denovo_lgds',
              description: 'de Novo LGDs',
              displayName: 'dn LGDs',
              effects: [
                'LGDs'
              ],
              category: 'denovo',
              defaultVisible: true,
              scores: [],
              variantTypes: []
            }
          ]
        }
      ],
      statistics: []
    }
  ],
  order: [
    { section: null, id: 'autism_gene_sets_rank' },
    { section: 'genomicScores', id: 'autism_scores' },
    { section: 'datasets', id: 'sequencing_de_novo' }
  ],
  pageSize: 5
};

class GeneProfilesServiceMock {
  public getConfig(): Observable<GeneProfilesSingleViewConfig> {
    return of(config);
  }
}

/* eslint-disable max-len */
const geneColumn = new GeneProfilesColumn('createTab', [], 'Gene', false, 'geneSymbol', null, false, true);
const geneSetSetsCol = new GeneProfilesColumn(null, [], 'SFARI ALL', true, 'autism_gene_sets_rank.SFARI ALL', null, true, true);
const geneSetCol = new GeneProfilesColumn(null, [geneSetSetsCol], 'Autism Gene Sets', false, 'autism_gene_sets_rank', null, true, true);
const geneScoreScoresCol = new GeneProfilesColumn(null, [], 'SFARI gene score', true, 'autism_scores.SFARI gene score', null, true, true);
const geneScoreCol = new GeneProfilesColumn(null, [geneScoreScoresCol], 'Autism Scores', false, 'autism_scores', null, false, true);
const datasetPersonSetsStatisticsCol = new GeneProfilesColumn('goToQuery', [], 'dn LGDs', false, 'sequencing_de_novo.autism.denovo_lgds', null, true, true);
const datasetPersonSetsCol = new GeneProfilesColumn(null, [datasetPersonSetsStatisticsCol], 'autism (21775)', false, 'sequencing_de_novo.autism', null, false, true);
const datasetCol = new GeneProfilesColumn(null, [datasetPersonSetsCol], 'Sequencing de Novo', false, 'sequencing_de_novo', null, false, true);
/* eslint-enable max-len */

const geneProfilesTableConfigMock= new GeneProfilesTableConfig();
geneProfilesTableConfigMock.columns = [geneColumn, geneSetCol, geneScoreCol, datasetCol];
geneProfilesTableConfigMock.defaultDataset = 'mockDataset';
geneProfilesTableConfigMock.pageSize = 5;

describe('GeneProfilesBlockComponent', () => {
  let component: GeneProfilesBlockComponent;
  let fixture: ComponentFixture<GeneProfilesBlockComponent>;
  const geneProfilesServiceMock = new GeneProfilesServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneProfilesBlockComponent, GeneProfilesTableComponent, MultipleSelectMenuComponent, TruncatePipe],
      providers: [
        ConfigService,
        QueryService,
        DatasetsService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: GeneProfilesService, useValue: geneProfilesServiceMock }
      ],
      imports: [
        HttpClientTestingModule, NgbNavModule, RouterTestingModule, FormsModule,
        NgxsModule.forRoot([GeneProfilesState], {developmentMode: true})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should create gene profiles table configuration', () => {
    component.ngOnInit();
    expect(component.geneProfilesTableConfig).toStrictEqual(geneProfilesTableConfigMock);
    expect(component.geneProfilesTableSortBy).toBe('autism_gene_sets_rank');
    expect(component.geneProfilesSingleViewConfig).toStrictEqual(config);
  });
});
