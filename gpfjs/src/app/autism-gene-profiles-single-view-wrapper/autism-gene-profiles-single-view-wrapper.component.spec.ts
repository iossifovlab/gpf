import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { ActivatedRoute } from '@angular/router';
import { lastValueFrom, Observable, of } from 'rxjs';
import { AutismGeneProfileSingleViewWrapperComponent } from './autism-gene-profiles-single-view-wrapper.component';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';

class MockActivatedRoute {
  public params = {dataset: 'testDatasetId', get: (): string => ''};
  public parent = {params: of(this.params)};
  public queryParamMap = of(this.params);
  public snapshot = {params: {genes: 'ABC1,dEf2,'}};
}

class MockAutismGeneProfilesService {
  public getConfig(): Observable<object> {
    return of({defaultDataset: 'mockDataset'});
  }
}

describe('AutismGeneProfileSingleViewWrapperComponent', () => {
  let component: AutismGeneProfileSingleViewWrapperComponent;
  let fixture: ComponentFixture<AutismGeneProfileSingleViewWrapperComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AutismGeneProfileSingleViewWrapperComponent],
      providers: [
        ConfigService,
        {provide: AutismGeneProfilesService, useValue: new MockAutismGeneProfilesService()},
        {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
      ],
      imports: [HttpClientTestingModule]
    }).compileComponents();

    fixture = TestBed.createComponent(AutismGeneProfileSingleViewWrapperComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', async() => {
    component.ngOnInit();
    const config = await lastValueFrom(component.$autismGeneToolConfig);
    expect(config.defaultDataset).toBe('mockDataset');
  });

  it('should set gene symbols after view initialization', () => {
    expect(component.geneSymbols).toStrictEqual(new Set<string>());
    component.ngAfterViewInit();
    expect(component.geneSymbols).toStrictEqual(new Set<string>(['ABC1', 'dEf2']));
  });
});
