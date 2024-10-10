import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { GeneSetsComponent } from './gene-sets.component';
import { GeneSetsService } from './gene-sets.service';
import { NgbAccordionModule, NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { BrowserModule, By } from '@angular/platform-browser';
import { CommonModule, APP_BASE_HREF } from '@angular/common';
import { DenovoPersonSetCollection, GeneSet, GeneSetsCollection, GeneSetType } from './gene-sets';
import { Observable } from 'rxjs/internal/Observable';
import { of } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { geneSetsReducer } from './gene-sets.state';
import {
  MatAutocompleteOrigin,
  MatAutocomplete,
  MatAutocompleteTrigger,
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY } from '@angular/material/autocomplete';
import { StoreModule, Store } from '@ngrx/store';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';

class MockGeneSetsService {
  public provide = true;

  public getGeneSets(): Observable<GeneSet[]> {
    if (this.provide) {
      return of([new GeneSet('name1', 2, 'desc3', 'download4'), new GeneSet('name5', 6, 'desc7', 'download8')]);
    } else {
      return of(undefined);
    }
  }

  public getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    if (this.provide) {
      return of([
        new GeneSetsCollection('denovo', 'desc2',
          [
            new GeneSetType(
              'id3',
              'datasetName4',
              [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
            ),
            new GeneSetType(
              'id9',
              'datasetName10',
              [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])]
            )
          ]
        ),
        new GeneSetsCollection('name15', 'desc16',
          [
            new GeneSetType(
              'id17',
              'datasetName18',
              [new DenovoPersonSetCollection('personSetCollectionId19', 'personSetCollectionName20', [])]
            ),
            new GeneSetType(
              'id23',
              'datasetName24',
              [new DenovoPersonSetCollection('personSetCollectionId25', 'personSetCollectionName26', [])]
            )
          ]
        )
      ]);
    } else {
      return of(undefined);
    }
  }

  public getDenovoGeneSets(): Observable<GeneSetType[]> {
    if (this.provide) {
      return of([
        new GeneSetType(
          'id3',
          'datasetName4',
          [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
        ),
        new GeneSetType(
          'id9',
          'datasetName10',
          [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])]
        ),
    
        new GeneSetType(
          'id17',
          'datasetName18',
          [new DenovoPersonSetCollection('personSetCollectionId19', 'personSetCollectionName20', [])]
        ),
        new GeneSetType(
          'id23',
          'datasetName24',
          [new DenovoPersonSetCollection('personSetCollectionId25', 'personSetCollectionName26', [])]
        )
      ]);
    } else {
      return of(undefined);
    }
  }
}

describe('GeneSetsComponent', () => {
  let component: GeneSetsComponent;
  let fixture: ComponentFixture<GeneSetsComponent>;
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSetsComponent],
      imports: [
        StoreModule.forRoot({geneSets: geneSetsReducer}),
        HttpClientTestingModule, RouterTestingModule,
        NgbAccordionModule, NgbNavModule,
        CommonModule,
        BrowserModule,
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger
      ],
      providers: [
        ConfigService, GeneSetsService, UsersService, DatasetsTreeService,
        { provide: APP_BASE_HREF, useValue: '' },
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''}
      ], schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneSetsComponent);
    component = fixture.componentInstance;

    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of());
    jest.spyOn(store, 'dispatch').mockReturnValue(null);

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should change the gene set', () => {
    const geneSetMock1 = new GeneSet('name1', 1, 'desc1', 'download1');
    component.selectedGeneSet = geneSetMock1;
    expect(component.selectedGeneSet).toStrictEqual(GeneSet.fromJson({
      name: 'name1',
      count: 1,
      desc: 'desc1',
      download: 'download1'
    }));

    const geneSetMock2 = new GeneSet('name2', 3, 'desc4', 'download5');
    component.selectedGeneSet = geneSetMock2;
    expect(component.selectedGeneSet).toStrictEqual(GeneSet.fromJson({
      name: 'name2',
      count: 3,
      desc: 'desc4',
      download: 'download5'
    }));
  });

  it('should set and get selectedGeneSetsCollection', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType(
        'datasetId3',
        'datasetName4',
        [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6',[])]
      ),
      new GeneSetType(
        'datasetId9',
        'datasetName10',
        [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12',[])]
      )
    ]);

    component.selectedGeneSetsCollection = geneSetsCollectionMock1;

    expect(component.selectedGeneSetsCollection).toStrictEqual(GeneSetsCollection.fromJson({
      name: 'name1',
      desc: 'desc2',
      types: [
        new GeneSetType('datasetId3', 'datasetName4', [
          new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])
        ]),
        new GeneSetType('datasetId9', 'datasetName10', [
          new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])
        ])
      ]
    }));
  });

  it('should set and check if selectedGeneType has been set', () => {
    jest.useFakeTimers();

    component.setSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3', true);
    component.setSelectedGeneType('datasetId4', 'personSetCollectionId5', 'geneType6', false);
    jest.advanceTimersByTime(350);
    expect(component.isSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3')).toBe(true);
    expect(component.isSelectedGeneType('datasetId4', 'personSetCollectionId5', 'geneType6')).toBe(false);

    component.setSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3', false);
    jest.advanceTimersByTime(350);
    expect(component.isSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3')).toBe(false);
  });

  it('should set onSelect', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType('datasetId3', 'datasetName4', [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]),
      new GeneSetType('datasetId9', 'datasetName10', [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])])
    ]);

    component.selectedGeneSetsCollection = geneSetsCollectionMock1;
    const spy = jest.spyOn(component, 'onSearch');

    fixture.detectChanges();

    component.onSelect(new GeneSet('name1', 2, 'desc3', 'download4'));
    expect(component.selectedGeneSet).toStrictEqual(new GeneSet('name1', 2, 'desc3', 'download4'));
    expect(spy).not.toHaveBeenCalledWith();

    component.onSelect(null);
    expect(spy).toHaveBeenCalledWith();
  });

  it('should set onSearch', () => {
    component.selectedGeneSetsCollection = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType('datasetId1', 'datasetName2', [new DenovoPersonSetCollection('personSetCollectionId3', 'personSetCollectionName4', [])]),
      new GeneSetType('datasetId7', 'datasetName8', [new DenovoPersonSetCollection('personSetCollectionId9', 'personSetCollectionName10', [])]),
    ]);

    component.geneSets = [
      new GeneSet('name13', 14, 'desc15', 'download16'),
      new GeneSet('name17', 18, 'desc19', 'download20')
    ];
    component.searchQuery = 'name15';
    component.onSearch();
    expect(component.searchQuery).toBe('name15');
    expect(component.geneSets).toStrictEqual([]);

    component.geneSets = [
      new GeneSet('name13', 14, 'desc15', 'download16'),
      new GeneSet('name17', 18, 'desc19', 'download20'),
      new GeneSet('name17', 21, 'desc20', 'download21')
    ];
    component.searchQuery = 'name17';
    component.onSearch();
    expect(component.geneSets).toStrictEqual([
      new GeneSet('name17', 18, 'desc19', 'download20'),
      new GeneSet('name17', 21, 'desc20', 'download21')]);
  });
});
