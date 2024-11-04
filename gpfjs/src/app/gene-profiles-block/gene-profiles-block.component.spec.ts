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
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { FormsModule } from '@angular/forms';
import { APP_BASE_HREF } from '@angular/common';
import { GeneProfilesService } from './gene-profiles.service';
import { Observable, of } from 'rxjs';
import { GeneProfilesSingleViewConfig } from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { TruncatePipe } from '../utils/truncate.pipe';
import { GeneProfilesColumn, GeneProfilesTableConfig } from 'app/gene-profiles-table/gene-profiles-table';
import { geneProfilesReducer } from 'app/gene-profiles-table/gene-profiles-table.state';
import { cloneDeep } from 'lodash';
import { Store, StoreModule } from '@ngrx/store';
import { User } from 'app/users/users';
import { GeneProfileSingleViewComponent } from 'app/gene-profiles-single-view/gene-profiles-single-view.component';


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

class UsersServiceMock {
  public cachedUserInfo(): object {
    return {loggedIn: true};
  }

  public getUserInfoObservable(): Observable<object> {
    return of({});
  }

  public getUserInfo(): Observable<User> {
    return of(new User(
      1,
      'userMame',
      'userEmail',
      ['group'],
      true,
      [{datasetId: 'datasetId', datasetName: 'datasetName'}]
    ));
  }
}

/* eslint-disable @stylistic/max-len */
const geneColumn = new GeneProfilesColumn('createTab', [], 'Gene', false, 'geneSymbol', null, false, true);
const geneSetSetsCol = new GeneProfilesColumn(null, [], 'SFARI ALL', true, 'autism_gene_sets_rank.SFARI ALL', null, true, true);
const geneSetCol = new GeneProfilesColumn(null, [geneSetSetsCol], 'Autism Gene Sets', false, 'autism_gene_sets_rank', null, true, true);
const geneScoreScoresCol = new GeneProfilesColumn(null, [], 'SFARI gene score', true, 'autism_scores.SFARI gene score', null, true, true);
const geneScoreCol = new GeneProfilesColumn(null, [geneScoreScoresCol], 'Autism Scores', false, 'autism_scores', null, false, true);
const datasetPersonSetsStatisticsCol = new GeneProfilesColumn('goToQuery', [], 'dn LGDs', false, 'sequencing_de_novo.autism.denovo_lgds', null, true, true);
const datasetPersonSetsCol = new GeneProfilesColumn(null, [datasetPersonSetsStatisticsCol], 'autism (21775)', false, 'sequencing_de_novo.autism', null, false, true);
const datasetCol = new GeneProfilesColumn(null, [datasetPersonSetsCol], 'Sequencing de Novo', false, 'sequencing_de_novo', null, false, true);
/* eslint-enable @stylistic/max-len */

const geneProfilesTableConfigMock= new GeneProfilesTableConfig();
geneProfilesTableConfigMock.columns = [geneColumn, geneSetCol, geneScoreCol, datasetCol];
geneProfilesTableConfigMock.defaultDataset = 'mockDataset';
geneProfilesTableConfigMock.pageSize = 5;

describe('GeneProfilesBlockComponent', () => {
  let component: GeneProfilesBlockComponent;
  let fixture: ComponentFixture<GeneProfilesBlockComponent>;
  const geneProfilesServiceMock = new GeneProfilesServiceMock();
  const usersServiceMock = new UsersServiceMock();
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneProfilesBlockComponent, GeneProfilesTableComponent, MultipleSelectMenuComponent, TruncatePipe],
      providers: [
        ConfigService,
        QueryService,
        DatasetsService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: GeneProfilesService, useValue: geneProfilesServiceMock },
        { provide: UsersService, useValue: usersServiceMock }
      ],
      imports: [
        HttpClientTestingModule, NgbNavModule, RouterTestingModule, FormsModule,
        StoreModule.forRoot({geneProfiles: geneProfilesReducer})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneProfilesBlockComponent);
    component = fixture.componentInstance;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should create gene profiles table configuration', () => {
    component.ngOnInit();
    expect(component.geneProfilesTableConfig).toStrictEqual(geneProfilesTableConfigMock);
    expect(component.geneProfilesSingleViewConfig).toStrictEqual(config);
  });

  it('should reset table configuration', () => {
    component.ngOnInit();
    const oldTableConfig = cloneDeep(component.geneProfilesTableConfig);

    component.geneProfilesTableConfig.columns = [];

    expect(component.geneProfilesTableConfig).not.toStrictEqual(oldTableConfig);
    component.resetConf();
    expect(component.geneProfilesTableConfig).toStrictEqual(oldTableConfig);
  });

  it('should handle table value click event', () => {
    const goToQuerySpy = jest.spyOn(GeneProfileSingleViewComponent, 'goToQuery').mockImplementation();
    const args = {
      geneSymbol: 'chd8',
      statisticId: 'sequencing_de_novo.autism.denovo_lgds',
      newTab: false
    };
    component.goToQueryEventHandler(args);
    expect(goToQuerySpy).toHaveBeenCalledWith(
      store,
      component['queryService'],
      'chd8',
      {
        childrenCount: 21775,
        collectionId: 'phenotype',
        defaultVisible: true,
        description: '',
        displayName: 'autism',
        id: 'autism',
        parentsCount: 9836,
        shown: [],
        statistics: [{
          category: 'denovo',
          defaultVisible: true,
          description: 'de Novo LGDs',
          displayName: 'dn LGDs',
          effects: ['LGDs'],
          id: 'denovo_lgds',
          scores: [],
          variantTypes: []}
        ]},
      'sequencing_de_novo',
      {
        category: 'denovo',
        defaultVisible: true,
        description: 'de Novo LGDs',
        displayName: 'dn LGDs',
        effects: ['LGDs'],
        id: 'denovo_lgds',
        scores: [],
        variantTypes: []
      },
      false
    );
  });
});
