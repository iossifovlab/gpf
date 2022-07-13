import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { ActivatedRoute } from '@angular/router';
import { Observable, of } from 'rxjs';
import { AutismGeneProfileSingleViewWrapperComponent } from './autism-gene-profiles-single-view-wrapper.component';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';

class MockActivatedRoute {
  params = {dataset: 'testDatasetId', get: () => ''};
  parent = {params: of(this.params)};
  queryParamMap = of(this.params);
  snapshot = {params: {genes: 'abc1,def2,'}};
}

class MockAutismGeneProfilesService {
  public getConfig(): Observable<object> {
    return of({defaultDataset: 'mockDataset'});
  }
}

describe('AutismGeneProfileSingleViewWrapperComponent', () => {
  let component: AutismGeneProfileSingleViewWrapperComponent;
  let fixture: ComponentFixture<AutismGeneProfileSingleViewWrapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [AutismGeneProfileSingleViewWrapperComponent],
      providers: [
        ConfigService,
        {provide: AutismGeneProfilesService, useValue: new MockAutismGeneProfilesService()},
        {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
      ],
      imports: [HttpClientTestingModule]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfileSingleViewWrapperComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', (done) => {
    component.ngOnInit();
    component.$autismGeneToolConfig.subscribe(config => {
      expect(config.defaultDataset).toEqual('mockDataset');
      done();
    });
  });

  it('should set gene symbols after view initialization', () => {
    expect(component.geneSymbols).toEqual(new Set<string>());
    component.ngAfterViewInit();
    expect(component.geneSymbols).toEqual(new Set<string>(['ABC1', 'DEF2']));
  });
});
