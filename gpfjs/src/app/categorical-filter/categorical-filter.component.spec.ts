import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { UsersService } from 'app/users/users.service';
import { CategoricalFilterComponent } from './categorical-filter.component';

describe('CategoricalFilterComponent', () => {
  let component: CategoricalFilterComponent;
  let fixture: ComponentFixture<CategoricalFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [CategoricalFilterComponent],
      providers: [DatasetsService, PhenoBrowserService, ConfigService, UsersService],
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CategoricalFilterComponent);
    component = fixture.componentInstance;
    component.categoricalFilterState = jasmine.createSpyObj('CategoricalFilterState', ['selection']);
    component.categoricalFilterState.selection = jasmine.createSpyObj('CategoricalSelection', ['selection']);
    component.categoricalFilter = jasmine.createSpyObj('CategoricalFilter', ['selection'], {'from': 'phenodb'});
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
