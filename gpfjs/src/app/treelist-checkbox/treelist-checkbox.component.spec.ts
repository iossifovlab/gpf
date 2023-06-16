import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { Dataset } from 'app/datasets/datasets';
import { StudyFiltersTreeComponent, findNodeById } from './treelist-checkbox.component';
import { FormsModule } from '@angular/forms';

const datasetNodeMock1 = new DatasetNode(new Dataset('id1',
  null, null, ['id11', 'id12'], null, null, null, null, null,
  null, null, null, null, null, null, null, null, null, null, null
), [
  new Dataset(
    'id2',
    null, null, ['id1', 'parent2'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  ),
  new Dataset(
    'id3',
    null, null, ['id1', 'parent3'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  ),
  new Dataset(
    'id4',
    null, null, ['id4', 'parent4'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  )
]);

describe('StudyFiltersTreeComponent', () => {
  let component: StudyFiltersTreeComponent;
  let fixture: ComponentFixture<StudyFiltersTreeComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [StudyFiltersTreeComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(StudyFiltersTreeComponent);
    component = fixture.componentInstance;
    component.data = datasetNodeMock1;
    component.selectedStudies = new Set('');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get all childrens of dataset', () => {
    const datasetNodeMock2 = new DatasetNode(new Dataset(
      'id2',
      null, null, ['id21', 'id22'], null, null, null, null, null,
      null, null, null, null, null, null, null, null, null, null, null
    ), [
      new Dataset(
        'id4',
        null, null, ['id23', 'id24'], null, null, null, null, null,
        null, null, null, null, null, null, null, null, null, null, null
      )
    ]);

    expect(component.getAllChildren([
      datasetNodeMock1, datasetNodeMock2
    ])).toStrictEqual(new Set<string>(['id2', 'id3']));
  });

  it('should test find node by id', () => {
    expect(findNodeById(datasetNodeMock1, 'id3')).toStrictEqual(new DatasetNode(
      new Dataset(
        'id3',
        null, null, ['id1', 'parent3'], null, null, null, null, null,
        null, null, null, null, null, null, null, null, null, null, null
      ), [
        new Dataset(
          'id2',
          null, null, ['id1', 'parent2'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null
        ),
        new Dataset(
          'id3',
          null, null, ['id1', 'parent3'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null
        ),
        new Dataset(
          'id4',
          null, null, ['id4', 'parent4'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null
        )]
    ));
  });
});
