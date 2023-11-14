import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { QueryService } from 'app/query/query.service';
import { RouterTestingModule } from '@angular/router/testing';
import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block.component';
import { AgpTableComponent } from 'app/autism-gene-profiles-table/autism-gene-profiles-table.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { NgxsModule } from '@ngxs/store';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { FormsModule } from '@angular/forms';
import { APP_BASE_HREF } from '@angular/common';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { Observable, of } from 'rxjs';
import { AgpSingleViewConfig } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { TruncatePipe } from '../utils/truncate.pipe';
import { AgpColumn, AgpTableConfig } from 'app/autism-gene-profiles-table/autism-gene-profiles-table';

const config = {
  shown: [],
  defaultDataset: 'mockDataset',
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

class AutismGeneProfilesServiceMock {
  public getConfig(): Observable<AgpSingleViewConfig> {
    return of(config);
  }
}

/* eslint-disable max-len */
const geneColumn = new AgpColumn('createTab', [], 'Gene', false, 'geneSymbol', null, false, true);
const geneSetSetsCol = new AgpColumn(null, [], 'SFARI ALL', true, 'autism_gene_sets_rank.SFARI ALL', null, true, true);
const geneSetCol = new AgpColumn(null, [geneSetSetsCol], 'Autism Gene Sets', false, 'autism_gene_sets_rank', null, true, true);
const geneScoreScoresCol = new AgpColumn(null, [], 'SFARI gene score', true, 'autism_scores.SFARI gene score', null, true, true);
const geneScoreCol = new AgpColumn(null, [geneScoreScoresCol], 'Autism Scores', false, 'autism_scores', null, false, true);
const datasetPersonSetsStatisticsCol = new AgpColumn('goToQuery', [], 'dn LGDs', false, 'sequencing_de_novo.autism.denovo_lgds', null, true, true);
const datasetPersonSetsCol = new AgpColumn(null, [datasetPersonSetsStatisticsCol], 'autism (21775)', false, 'sequencing_de_novo.autism', null, false, true);
const datasetCol = new AgpColumn(null, [datasetPersonSetsCol], 'Sequencing de Novo', false, 'sequencing_de_novo', null, false, true);
/* eslint-enable max-len */

const agpTableConfigMock= new AgpTableConfig();
agpTableConfigMock.columns = [geneColumn, geneSetCol, geneScoreCol, datasetCol];
agpTableConfigMock.defaultDataset = 'mockDataset';
agpTableConfigMock.pageSize = 5;

describe('AutismGeneProfilesBlockComponent', () => {
  let component: AutismGeneProfilesBlockComponent;
  let fixture: ComponentFixture<AutismGeneProfilesBlockComponent>;
  const autismGeneProfilesServiceMock = new AutismGeneProfilesServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AutismGeneProfilesBlockComponent, AgpTableComponent, MultipleSelectMenuComponent, TruncatePipe],
      providers: [
        ConfigService,
        QueryService,
        DatasetsService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: AutismGeneProfilesService, useValue: autismGeneProfilesServiceMock }
      ],
      imports: [
        HttpClientTestingModule, NgbNavModule, RouterTestingModule, FormsModule,
        NgxsModule.forRoot([], {developmentMode: true})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AutismGeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should create agp table configuration', () => {
    component.ngOnInit();
    expect(component.agpTableConfig).toStrictEqual(agpTableConfigMock);
    expect(component.agpTableSortBy).toBe('autism_gene_sets_rank');
    expect(component.agpSingleViewConfig).toStrictEqual(config);
  });
});
