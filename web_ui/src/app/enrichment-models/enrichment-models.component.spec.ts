import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EnrichmentModelsComponent } from './enrichment-models.component';
import { EnrichmentModels, EnrichmentModelsService } from './enrichment-models.service';
import { of } from 'rxjs/internal/observable/of';
import { ConfigService } from 'app/config/config.service';
import { Store, StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { EnrichmentModelsState, setEnrichmentModels } from './enrichment-models.state';


const backgroundsMock = [
  {
    id: 'hg38/enrichment/ur_synonymous_iWGS_v1_1',
    name: 'UR synonymous background from SPARK iWGS v1.1',
    description: 'Ultra rare synonymous enrichment background build from\nSPARK iWGS v1.1 on Jan 8th, 2024.\n'
  },
  {
    id: 'hg38/enrichment/ur_synonymous_AGRE_WG38_859',
    name: 'UR synonymous background from AGRE WGS CSHL',
    description: 'Ultra rare synonymous enrichment background build from\n AGRE WGS CSHL on Jan 16th, 2024.\n'
  }
];

const countingMock = [
  {
    id: 'enrichment_events_counting',
    name: 'Counting events',
    description: 'Counting events'
  },
  {
    id: 'enrichment_gene_counting',
    name: 'Counting affected genes',
    description: 'Counting affected genes'
  }
];

const enrichmentModelsMock: EnrichmentModels = {
  countings: countingMock,
  backgrounds: backgroundsMock,
  defaultBackground: 'hg38/enrichment/ur_synonymous_iWGS_v1_1',
  defaultCounting: 'enrichment_events_counting'
};

const enrichmentModelsStateMock: EnrichmentModelsState = {
  enrichmentBackgroundModel: 'hg38/enrichment/ur_synonymous_AGRE_WG38_859',
  enrichmentCountingModel: 'enrichment_gene_counting'
};

class EnrichmentModelsServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getBackgroundModels(datasetId: string): Observable<EnrichmentModels> {
    return of(enrichmentModelsMock);
  }
}

describe('EnrichmentModelsComponent', () => {
  let component: EnrichmentModelsComponent;
  let fixture: ComponentFixture<EnrichmentModelsComponent>;
  const enrichmentModelsServiceMock = new EnrichmentModelsServiceMock();
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EnrichmentModelsComponent],
      providers: [
        { provide: EnrichmentModelsService, useValue: enrichmentModelsServiceMock },
        ConfigService,
        provideHttpClient()
      ],
      imports: [StoreModule.forRoot({})]
    });
    fixture = TestBed.createComponent(EnrichmentModelsComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2', 'value3']));
    jest.spyOn(store, 'dispatch').mockImplementation();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should make query for background models and set background and counting', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    component.ngOnInit();
    expect(component.backgrounds).toStrictEqual(backgroundsMock);
    expect(component.countings).toStrictEqual(countingMock);
    expect(component.background).toStrictEqual(backgroundsMock[0]);
    expect(component.counting).toStrictEqual(countingMock[0]);
    expect(dispatchSpy).toHaveBeenCalledWith(setEnrichmentModels({
      enrichmentBackgroundModel: 'hg38/enrichment/ur_synonymous_iWGS_v1_1',
      enrichmentCountingModel: 'enrichment_events_counting'
    }));
  });

  it('should get background models from state and set background and counting', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(enrichmentModelsStateMock));
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    component.ngOnInit();
    expect(component.backgrounds).toStrictEqual(backgroundsMock);
    expect(component.countings).toStrictEqual(countingMock);
    expect(component.background).toStrictEqual(backgroundsMock[1]);
    expect(component.counting).toStrictEqual(countingMock[1]);
    expect(dispatchSpy).toHaveBeenCalledWith(setEnrichmentModels({
      enrichmentBackgroundModel: enrichmentModelsStateMock.enrichmentBackgroundModel,
      enrichmentCountingModel: enrichmentModelsStateMock.enrichmentCountingModel
    }));
  });

  it('should change background', () => {
    const mockBackgroundModels = [
      { id: 'name 1', description: 'name 2', name: 'name 3' },
      { id: 'name 1', description: 'name 2', name: 'name 3' },
    ];

    const selectedBackground = mockBackgroundModels[1];

    component.background = { id: '1', name: 'Background Model 1', description: 'name 2' };
    component.counting = { id: '2', name: 'Background Model 2', description: 'name 3' };
    component.changeBackground({name: 'name 3', id: 'name 1', description: 'name 2' });

    expect(component.background).toStrictEqual(selectedBackground);
  });

  it('should change counting', () => {
    component.background = { id: '1', name: 'Background Model 1', description: 'name 2' };
    component.counting = { id: '2', name: 'Background Model 2', description: 'name 3' };
    component.changeCounting({name: 'name', id: 'name', description: 'name' });

    expect(component.counting).toStrictEqual({name: 'name', id: 'name', description: 'name'});
  });
});
