import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { GeneSetsComponent } from './gene-sets.component';
import { GeneSetsService } from './gene-sets.service';
import { NgbAccordionModule } from '@ng-bootstrap/ng-bootstrap';
import { CommonModule } from '@angular/common';
import { BrowserModule } from '@angular/platform-browser';
import { GeneSet, GeneSetsCollection, GeneSetType } from './gene-sets';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('GeneSetsComponent', () => {
  let component: GeneSetsComponent;
  let fixture: ComponentFixture<GeneSetsComponent>;
  const datasetsServiceMock = new MockDatasetsService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [],
      imports: [
        NgxsModule.forRoot([], {developmentMode: true}),
        HttpClientTestingModule, RouterTestingModule,
        NgbAccordionModule,
        CommonModule,
        BrowserModule
      ],
      providers: [
        ConfigService, GeneSetsService, { provide: DatasetsService, useValue: datasetsServiceMock }, UsersService
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneSetsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should change the gene set', () => {
    const geneSetMock1 = new GeneSet('name1', 1, 'desc1', 'download1');
    component.selectedGeneSet = geneSetMock1;
    expect(component.selectedGeneSet).toEqual(GeneSet.fromJson({
      name: 'name1',
      count: 1,
      desc: 'desc1',
      download: 'download1'
    }));

    const geneSetMock2 = new GeneSet('name2', 3, 'desc4', 'download5');
    component.selectedGeneSet = geneSetMock2;
    expect(component.selectedGeneSet).toEqual(GeneSet.fromJson({
      name: 'name2',
      count: 3,
      desc: 'desc4',
      download: 'download5'
    }));
  });

  it('should set and get selectedGeneSetsCollection', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType('datasetId3', 'datasetName4', 'personSetCollectionId5', 'personSetCollectionName6',
        ['personSetCollectionLegend7', 'personSetCollectionLegend8']),
      new GeneSetType('datasetId9', 'datasetName10', 'personSetCollectionId11', 'personSetCollectionName12',
        ['personSetCollectionLegend13', 'personSetCollectionLegend14'])
    ]);

    component.selectedGeneSetsCollection = geneSetsCollectionMock1;

    expect(component.selectedGeneSetsCollection).toEqual(GeneSetsCollection.fromJson({
      name: 'name1', desc: 'desc2',
      types: [{
        datasetId: 'datasetId3',
        datasetName: 'datasetName4',
        personSetCollectionId: 'personSetCollectionId5',
        personSetCollectionName: 'personSetCollectionName6',
        personSetCollectionLegend: ['personSetCollectionLegend7', 'personSetCollectionLegend8']
      }, {
        datasetId: 'datasetId9',
        datasetName: 'datasetName10',
        personSetCollectionId: 'personSetCollectionId11',
        personSetCollectionName: 'personSetCollectionName12',
        personSetCollectionLegend: ['personSetCollectionLegend13', 'personSetCollectionLegend14']
      }
      ]
    }));
  });

  it('should set and check if selectedGeneType has been set', () => {
    component.setSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3', true);
    component.setSelectedGeneType('datasetId4', 'personSetCollectionId5', 'geneType6', false);

    expect(component.isSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3')).toBe(true);
    expect(component.isSelectedGeneType('datasetId4', 'personSetCollectionId5', 'geneType6')).toBe(false);

    component.setSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3', false);
    expect(component.isSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3')).toBe(false);
  });

  it('should set onSelect', () => {
    const spy = jest.spyOn(component, 'onSearch');
    component.onSelect(new GeneSet('name1', 2, 'desc3', 'download4'));
    expect(component.selectedGeneSet).toEqual(new GeneSet('name1', 2, 'desc3', 'download4'));
    expect(spy).not.toHaveBeenCalledWith();

    component.onSelect(null);
    expect(spy).toHaveBeenCalled();
  });

  it('should set onSearch', () => {
    component.selectedGeneSetsCollection = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType('datasetId1', 'datasetName2', 'personSetCollectionId3', 'personSetCollectionName4', [
        'personSetCollectionLegend5', 'personSetCollection6'
      ]),
      new GeneSetType('datasetId7', 'datasetName8', 'personSetCollectionId9', 'personSetCollectionName10', [
        'personSetCollectionLegend11', 'personSetCollection12'
      ])
    ]);

    component.geneSets = [
      new GeneSet('name13', 14, 'desc15', 'download16'),
      new GeneSet('name17', 18, 'desc19', 'download20')
    ];
    component.onSearch('name15');
    expect(component.searchQuery).toEqual('name15');
    expect(component.geneSets).toEqual([]);

    component.geneSets = [
      new GeneSet('name13', 14, 'desc15', 'download16'),
      new GeneSet('name17', 18, 'desc19', 'download20'),
      new GeneSet('name17', 21, 'desc20', 'download21')
    ];
    component.onSearch('name17');
    expect(component.geneSets).toEqual([
      new GeneSet('name17', 18, 'desc19', 'download20'),
      new GeneSet('name17', 21, 'desc20', 'download21')]);
  });
});
