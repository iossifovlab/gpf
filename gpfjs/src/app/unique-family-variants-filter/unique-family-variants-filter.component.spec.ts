import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UniqueFamilyVariantsFilterComponent } from './unique-family-variants-filter.component';
import { NgxsModule } from '@ngxs/store';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';

class DatasetsServiceMock {
  public getSelectedDataset() {
    return {parents: []};
  }
}

describe('UniqueFamilyVariantsFilterComponent', () => {
  let component: UniqueFamilyVariantsFilterComponent;
  let fixture: ComponentFixture<UniqueFamilyVariantsFilterComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [UniqueFamilyVariantsFilterComponent],
      providers: [{provide: DatasetsService, useValue: new DatasetsServiceMock()}],
      imports: [HttpClientModule, NgxsModule.forRoot([], {developmentMode: true}), FormsModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(UniqueFamilyVariantsFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
