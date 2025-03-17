import { APP_BASE_HREF } from '@angular/common';
import { HttpClient, HttpHandler } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { DatasetNodeComponent } from './dataset-node.component';
import { Store, StoreModule } from '@ngrx/store';
import { DatasetNode } from './dataset-node';
import { Dataset } from 'app/datasets/datasets';
import { of } from 'rxjs';
import { setExpandedDatasets } from './dataset-node.state';

const datasetNodeMock = new DatasetNode(
  new Dataset('id1',
    null, ['id11', 'id12'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  ), [
    new Dataset(
      'id2',
      null, ['id1', 'parent2'], null, null, null, null, null,
      null, null, null, null, null, null, null, null, null, null, null
    ),
    new Dataset(
      'id3',
      null, ['id1', 'parent3'], null, null, null, null, null,
      null, null, null, null, null, null, null, null, null, null, null
    ),
    new Dataset(
      'id4',
      null, ['id4', 'parent4'], null, null, null, null, null,
      null, null, null, null, null, null, null, null, null, null, null
    )
  ]);
describe('DatasetNodeComponent', () => {
  let component: DatasetNodeComponent;
  let fixture: ComponentFixture<DatasetNodeComponent>;
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DatasetNodeComponent],
      providers: [
        DatasetsService, HttpClient, HttpHandler, ConfigService,
        UsersService, { provide: APP_BASE_HREF, useValue: '' },
      ],
      imports: [RouterTestingModule, StoreModule.forRoot({})]
    }).compileComponents();

    fixture = TestBed.createComponent(DatasetNodeComponent);
    component = fixture.componentInstance;

    component.datasetNode = datasetNodeMock;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with state data', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of('id1')).mockReturnValueOnce(of(['id1']));
    const setExpandabilitySpy = jest.spyOn(component, 'setExpandability');
    component.isExpanded = false;

    component.ngOnInit();

    expect(component.selectedDatasetId).toBe('id1');
    expect(setExpandabilitySpy).toHaveBeenCalledWith();
    expect(component.isExpanded).toBe(true);
  });

  it('should add to state', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['id1']));
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component['addToState']('idNew');
    expect(dispatchSpy).toHaveBeenCalledWith(setExpandedDatasets({expandedDatasets: ['id1', 'idNew']}));
  });

  it('should remove from state', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['id1', 'idRemove']));
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component['removeFromState']('idRemove');
    expect(dispatchSpy).toHaveBeenCalledWith(setExpandedDatasets({expandedDatasets: ['id1']}));
  });

  it('should update state', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['id1', 'idRemove']));
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component['updateState']('idRemove');
    expect(dispatchSpy).toHaveBeenCalledWith(setExpandedDatasets({expandedDatasets: ['id1']}));

    jest.spyOn(store, 'select').mockReturnValueOnce(of(['id1']));
    component['updateState']('idNew');
    expect(dispatchSpy).toHaveBeenCalledWith(setExpandedDatasets({expandedDatasets: ['id1', 'idNew']}));
  });

  it('should set expanded status', () => {
    const setExpandabilitySpy = jest.spyOn(component, 'setExpandability');

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const addToStateSpy = jest.spyOn(component as any, 'addToState'); // spy private method
    component.isExpanded = false;

    component.setIsExpanded();
    expect(component.isExpanded).toBe(true);
    expect(addToStateSpy).toHaveBeenCalledWith('id1');
    expect(setExpandabilitySpy).toHaveBeenCalledWith();
  });

  it('should toggle datasets', () => {
    const emitEventToChildSpy = jest.spyOn(component, 'emitEventToChild');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const updateStateSpy = jest.spyOn(component as any, 'updateState');
    component.isExpanded = true;

    component.toggleDatasetCollapse('id2');
    expect(updateStateSpy).toHaveBeenCalledWith('id2');
    expect(emitEventToChildSpy).toHaveBeenCalledWith();
  });

  it('should open dataset', () => {
    const routerSpy = jest.spyOn(component['router'], 'navigate');
    component.select();
    expect(routerSpy).toHaveBeenCalledWith(['/datasets/id1']);
  });

  it('should not open already loaded dataset', () => {
    const routerSpy = jest.spyOn(component['router'], 'navigate');
    component.selectedDatasetId = 'id1';
    component.select();
    expect(routerSpy).not.toHaveBeenCalledWith(['/datasets/id1']);
  });

  it('should open dataset in new tab', () => {
    const windowOpenSpy = jest.spyOn(window, 'open');
    const windowMock = { url: '/some/url', location: { assign: jest.fn() } } as unknown as Window;
    windowOpenSpy.mockReturnValueOnce(windowMock);

    component.select(true);
    expect(windowMock.location.assign).toHaveBeenCalledWith('/datasets/id1');
  });

  it('should not open dataset when dataset is invalid', () => {
    const windowOpenSpy = jest.spyOn(window, 'open');
    const routerSpy = jest.spyOn(component['router'], 'navigate');

    const windowMock = { url: '/some/url', location: { assign: jest.fn() } } as unknown as Window;
    windowOpenSpy.mockReturnValueOnce(windowMock);

    component.datasetNode.dataset = null;
    component.select();
    expect(routerSpy).not.toHaveBeenCalledWith();
    expect(windowMock.location.assign).not.toHaveBeenCalledWith();
  });
});

