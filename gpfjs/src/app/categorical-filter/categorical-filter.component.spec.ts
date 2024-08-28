import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { UsersService } from 'app/users/users.service';
import { CategoricalFilterComponent } from './categorical-filter.component';
import { APP_BASE_HREF } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';

describe('CategoricalFilterComponent', () => {
  let component: CategoricalFilterComponent;
  let fixture: ComponentFixture<CategoricalFilterComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CategoricalFilterComponent],
      providers: [
        DatasetsService,
        PhenoBrowserService,
        ConfigService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule, FormsModule,
        StoreModule.forRoot({datasetId: datasetIdReducer})
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
