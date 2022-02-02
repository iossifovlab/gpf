import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { AutismGeneProfileSingleViewWrapperComponent } from './autism-gene-profiles-single-view-wrapper.component';

class MockActivatedRoute {
  params = {dataset: 'testDatasetId', get: () => ''};
  parent = {params: of(this.params)};
  queryParamMap = of(this.params);
  snapshot = {params: {genes: 'mockGeneSymbol'}};
}

describe('AutismGeneProfileSingleViewWrapperComponent', () => {
  let component: AutismGeneProfileSingleViewWrapperComponent;
  let fixture: ComponentFixture<AutismGeneProfileSingleViewWrapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [AutismGeneProfileSingleViewWrapperComponent],
      providers: [
        ConfigService,
        {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
      ],
      imports: [HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfileSingleViewWrapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
