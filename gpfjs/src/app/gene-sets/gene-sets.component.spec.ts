import { HttpClientTestingModule } from "@angular/common/http/testing";
import { ComponentFixture, TestBed, waitForAsync } from "@angular/core/testing";
import { RouterTestingModule } from "@angular/router/testing";
import { NgxsModule, Store } from "@ngxs/store";
import { ConfigService } from "app/config/config.service";
import { DatasetsService } from "app/datasets/datasets.service";
import { UsersService } from "app/users/users.service";
import { GeneSetsComponent } from "./gene-sets.component";
import { GeneSetsService } from "./gene-sets.service";
import { NgbAccordionModule } from "@ng-bootstrap/ng-bootstrap"
import { CommonModule } from "@angular/common";
import { BrowserModule } from "@angular/platform-browser";
import { GeneSet, GeneSetsCollection, GeneSetType } from "./gene-sets";

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
            imports: [NgxsModule.forRoot([], {developmentMode: true}), HttpClientTestingModule, RouterTestingModule, NgbAccordionModule, CommonModule, BrowserModule],
            providers: [ConfigService, GeneSetsService, { provide: DatasetsService, useValue: datasetsServiceMock }, UsersService]
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
            'name': 'name1',
            'count': 1,
            'desc': 'desc1',
            'download': 'download1'
        }));
        
        const geneSetMock2 = new GeneSet('name2', 3, 'desc4', 'download5');
        component.selectedGeneSet = geneSetMock2;
        expect(component.selectedGeneSet).toEqual(GeneSet.fromJson({
            'name': 'name2',
            'count': 3,
            'desc': 'desc4',
            'download': 'download5'
        }));
    });

    it('should test selectedGeneSetsCollection', () => {
        const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
            new GeneSetType('datasetId3', 'datasetName4', 'personSetCollectionId5', 'personSetCollectionName6', ['personSetCollectionLegend7', 'personSetCollectionLegend8']),
            new GeneSetType('datasetId9', 'datasetName10', 'personSetCollectionId11', 'personSetCollectionName12', ['personSetCollectionLegend13', 'personSetCollectionLegend14'])
        ]);

        component.selectedGeneSetsCollection = geneSetsCollectionMock1;

        expect(component.selectedGeneSetsCollection).toEqual(GeneSetsCollection.fromJson({
            'name': 'name1', 'desc':'desc2', 
            'types': [{
                    'datasetId': 'datasetId3', 'datasetName': 'datasetName4', 'personSetCollectionId': 'personSetCollectionId5', 'personSetCollectionName': 'personSetCollectionName6',
                    'personSetCollectionLegend': [ 'personSetCollectionLegend7', 'personSetCollectionLegend8' ] 
                }, {
                    'datasetId': 'datasetId9', 'datasetName':'datasetName10', 'personSetCollectionId':'personSetCollectionId11', 'personSetCollectionName': 'personSetCollectionName12', 
                    'personSetCollectionLegend': [ 'personSetCollectionLegend13', 'personSetCollectionLegend14' ]
                }
            ]
        }))
    });

});