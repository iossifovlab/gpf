import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { UsersService } from 'app/users/users.service';
import { CategoricalFilterComponent } from './categorical-filter.component';
import { APP_BASE_HREF } from '@angular/common';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('CategoricalFilterComponent', () => {
  let component: CategoricalFilterComponent;
  let fixture: ComponentFixture<CategoricalFilterComponent>;
  const datasetsServiceMock = new MockDatasetsService();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CategoricalFilterComponent],
      providers: [
        { provide: DatasetsService, useValue: datasetsServiceMock },
        PhenoBrowserService,
        ConfigService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule, FormsModule,
        NgxsModule.forRoot([], {developmentMode: true})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CategoricalFilterComponent);
    component = fixture.componentInstance;
    (component.categoricalFilter as any) = {from: 'phenodb'};
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
