import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EnrichmentModelsComponent } from './enrichment-models.component';
import { EnrichmentModelsService } from './enrichment-models.service';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs/internal/observable/of';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';

describe('EnrichmentModelsComponent', () => {
  let component: EnrichmentModelsComponent;
  let fixture: ComponentFixture<EnrichmentModelsComponent>;
  // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
  let enrichmentModelsService: EnrichmentModelsService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EnrichmentModelsComponent],
      providers: [EnrichmentModelsService, ConfigService, FullscreenLoadingService],
      imports: [NgxsModule.forRoot([], {developmentMode: true}), HttpClientTestingModule]
    });
    fixture = TestBed.createComponent(EnrichmentModelsComponent);
    component = fixture.componentInstance;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    component['store'] = {
      // eslint-disable-next-line prefer-arrow/prefer-arrow-functions, no-unused-vars, @typescript-eslint/no-unused-vars
      selectOnce: function(_: unknown) {
        return of({effectTypes: ['value1', 'value2', 'value3']});
      },
      // eslint-disable-next-line max-len
      // eslint-disable-next-line prefer-arrow/prefer-arrow-functions, no-unused-vars, @typescript-eslint/no-unused-vars, @typescript-eslint/no-empty-function
      dispatch: function(_: unknown) {}
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any;
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
