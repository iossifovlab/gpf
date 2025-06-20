import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UniqueFamilyVariantsFilterComponent } from './unique-family-variants-filter.component';
import { FormsModule } from '@angular/forms';
import { provideHttpClient } from '@angular/common/http';
import { DatasetsService } from 'app/datasets/datasets.service';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { ConfigService } from 'app/config/config.service';
import { Store, StoreModule } from '@ngrx/store';
import {
  setUniqueFamilyVariantsFilter,
  uniqueFamilyVariantsFilterReducer
} from './unique-family-variants-filter.state';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { of } from 'rxjs';

class DatasetsServiceMock {
  public getSelectedDataset(): object {
    return {parents: []};
  }
}

class MockDatasetsTreeService {
  public getUniqueLeafNodes(): Set<string> {
    return new Set(['child1', 'child2', 'child3']);
  }
}

describe('UniqueFamilyVariantsFilterComponent', () => {
  let component: UniqueFamilyVariantsFilterComponent;
  let fixture: ComponentFixture<UniqueFamilyVariantsFilterComponent>;
  let store: Store;
  const datasetsTreeServiceMock = new MockDatasetsTreeService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [UniqueFamilyVariantsFilterComponent],
      providers: [
        { provide: DatasetsService, useValue: new DatasetsServiceMock() },
        DatasetsTreeService,
        ConfigService,
        provideHttpClient(),
        { provide: DatasetsTreeService, useValue: datasetsTreeServiceMock },
      ],
      imports: [
        StoreModule.forRoot({
          uniqueFamilyVariantsFilter: uniqueFamilyVariantsFilterReducer,
          datasetId: datasetIdReducer}),
        FormsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UniqueFamilyVariantsFilterComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get unique family variants from state on changes', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of(true));
    component.ngOnChanges();
    expect(component.filterValue).toBe(true);
  });

  it('should get unique family variants from state on init', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of(true));
    component.ngOnInit();
    expect(component.filterValue).toBe(true);
  });

  it('should check if unique family variants filter is visible when selected dataset has children', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of('datasetId'));
    component.ngOnInit();
    expect(component.isVisible).toBe(true);
  });

  it('should get unique family variants value default value', () => {
    expect(component.filterValue).toBe(false);
  });

  it('should set unique family variants value', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.filterValue = true;
    expect(dispatchSpy).toHaveBeenCalledWith(setUniqueFamilyVariantsFilter({uniqueFamilyVariantsFilter: true}));
  });
});
