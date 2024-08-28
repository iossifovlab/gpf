import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UniqueFamilyVariantsFilterComponent } from './unique-family-variants-filter.component';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { DatasetsService } from 'app/datasets/datasets.service';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { ConfigService } from 'app/config/config.service';
import { StoreModule } from '@ngrx/store';

class DatasetsServiceMock {
  public getSelectedDataset(): object {
    return {parents: []};
  }
}

describe('UniqueFamilyVariantsFilterComponent', () => {
  let component: UniqueFamilyVariantsFilterComponent;
  let fixture: ComponentFixture<UniqueFamilyVariantsFilterComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [UniqueFamilyVariantsFilterComponent],
      providers: [{provide: DatasetsService, useValue: new DatasetsServiceMock()}, DatasetsTreeService, ConfigService],
      imports: [HttpClientModule, StoreModule.forRoot({}), FormsModule]
    }).compileComponents();

    fixture = TestBed.createComponent(UniqueFamilyVariantsFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
