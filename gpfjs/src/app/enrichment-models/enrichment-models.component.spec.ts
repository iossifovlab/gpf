import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EnrichmentModelsComponent } from './enrichment-models.component';
import { EnrichmentModelsService } from './enrichment-models.service';
import { of } from 'rxjs/internal/observable/of';
import { ConfigService } from 'app/config/config.service';
import { Store, StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';

describe('EnrichmentModelsComponent', () => {
  let component: EnrichmentModelsComponent;
  let fixture: ComponentFixture<EnrichmentModelsComponent>;
  // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
  let enrichmentModelsService: EnrichmentModelsService;
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EnrichmentModelsComponent],
      providers: [EnrichmentModelsService, ConfigService, provideHttpClient()],
      imports: [StoreModule.forRoot({})]
    });
    fixture = TestBed.createComponent(EnrichmentModelsComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2', 'value3']));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    enrichmentModelsService = TestBed.inject(EnrichmentModelsService);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
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
