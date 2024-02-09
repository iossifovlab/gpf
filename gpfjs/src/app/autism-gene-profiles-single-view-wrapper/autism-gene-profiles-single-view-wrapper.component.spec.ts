import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { ActivatedRoute } from '@angular/router';
import { lastValueFrom, Observable, of } from 'rxjs';
import { GeneProfileSingleViewWrapperComponent } from './autism-gene-profiles-single-view-wrapper.component';
import { GeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';

class MockActivatedRoute {
  public params = {dataset: 'testDatasetId', get: (): string => ''};
  public parent = {params: of(this.params)};
  public queryParamMap = of(this.params);
  public snapshot = {params: {genes: 'aBc1,DeF2,'}};
}

class MockGeneProfilesService {
  public getConfig(): Observable<object> {
    return of({defaultDataset: 'mockDataset'});
  }
}

describe('GeneProfileSingleViewWrapperComponent', () => {
  let component: GeneProfileSingleViewWrapperComponent;
  let fixture: ComponentFixture<GeneProfileSingleViewWrapperComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneProfileSingleViewWrapperComponent],
      providers: [
        ConfigService,
        {provide: GeneProfilesService, useValue: new MockGeneProfilesService()},
        {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
      ],
      imports: [HttpClientTestingModule]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneProfileSingleViewWrapperComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', async() => {
    component.ngOnInit();
    const config = await lastValueFrom(component.$geneProfilesConfig);
    expect(config.defaultDataset).toBe('mockDataset');
  });

  it('should set gene symbols after view initialization', () => {
    expect(component.geneSymbols).toStrictEqual(new Set<string>());
    component.ngAfterViewInit();
    expect(component.geneSymbols).toStrictEqual(new Set<string>(['aBc1', 'DeF2']));
  });
});
