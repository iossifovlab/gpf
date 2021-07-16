import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';
import { GenotypeBrowserSingleViewComponent } from './genotype-browser-single-view.component';
import { ErrorsState } from 'app/common/errors.state';

class MockActivatedRoute {
  params = {dataset: 'testDatasetId', get: () => ''};
  parent = {params: of(this.params)};

  queryParamMap = of(this.params);
}

describe('GenotypeBrowserSingleViewComponent', () => {
  let component: GenotypeBrowserSingleViewComponent;
  let fixture: ComponentFixture<GenotypeBrowserSingleViewComponent>;

  const activatedRoute = new MockActivatedRoute();

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GenotypeBrowserSingleViewComponent],
      providers: [
        {provide: ActivatedRoute, useValue: activatedRoute},
      ],
      imports: [NgxsModule.forRoot([ErrorsState])],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypeBrowserSingleViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
