import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownModule } from 'ngx-markdown';
import { GenomicScoresComponent } from './genomic-scores.component';
import { PopupComponent } from 'app/popup/popup.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Store, StoreModule } from '@ngrx/store';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { GenomicScoreState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { MatMenuModule } from '@angular/material/menu';
import { setErrors } from 'app/common/errors.state';
import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';
import { CategoricalHistogram, NumberHistogram } from 'app/utils/histogram-types';
import { range } from 'lodash';

describe('GenomicScoresComponent', () => {
  let component: GenomicScoresComponent;
  let fixture: ComponentFixture<GenomicScoresComponent>;
  let store: Store;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [
        GenomicScoresComponent,
        PopupComponent,
        ErrorsAlertComponent,
      ],
      imports: [
        NgbModule,
        FormsModule,
        MarkdownModule.forRoot(),
        StoreModule.forRoot({}),
        MatMenuModule,
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
      .overrideModule(BrowserDynamicTestingModule, {
        set: {}
      })
      .compileComponents();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    fixture = TestBed.createComponent(GenomicScoresComponent);
    component = fixture.componentInstance;

    component.errors = [];
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment

    component.selectedGenomicScore = new GenomicScore(
      'desc',
      'help',
      'score',
      new CategoricalHistogram(
        [
          {name: 'name1', value: 10},
          {name: 'name2', value: 20},
          {name: 'name3', value: 30},
          {name: 'name4', value: 40},
          {name: 'name5', value: 50},
        ],
        ['name1', 'name2', 'name3', 'name4', 'name5'],
        'large value descriptions',
        'small value descriptions',
        true,
        0
      ),
    );
    component.initialState = {
      score: 'score',
      histogramType: 'categorical',
      rangeStart: null,
      rangeEnd: null,
      values: ['value1', 'value2', 'value3'],
      categoricalView: 'range selector',
    } as GenomicScoreState;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should dispatch histogram validation errors to state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.selectedGenomicScore = new GenomicScore(
      'desc',
      'help',
      'score',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 7, 8, true, true)
    );

    component.setHistogramValidationErrors(['Range start should be more than or equal to domain min.']);

    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'genomicScores: score', errors: ['Range start should be more than or equal to domain min.']
      }
    }));
  });

  it('should dispatch error message when score is invalid', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    const state: GenomicScoreState = {
      histogramType: 'categorical',
      score: '',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1'],
      categoricalView: 'click selector'
    };

    component.initialState = state;
    component.ngOnInit();
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'genomicScores: score', errors: [
          'Empty score names are invalid.'
        ]
      }
    }));
  });

  it('should reset state when switching categorical views', () => {
    const state: GenomicScoreState = {
      histogramType: 'categorical',
      score: 'score',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1'],
      categoricalView: 'range selector'
    };

    component.localState = state;
    component.switchCategoricalHistogramView('click selector');
    expect(component.localState.values).toStrictEqual([]);
    expect(component.localState.categoricalView).toBe('click selector');

    component.localState.values = ['val1', 'val2'];
    component.switchCategoricalHistogramView('dropdown selector');
    expect(component.localState.values).toStrictEqual([]);
    expect(component.localState.categoricalView).toBe('dropdown selector');

    component.localState.values = ['val1', 'val2'];
    component.switchCategoricalHistogramView('range selector');
    expect(component.localState.values).toStrictEqual(['name1', 'name2', 'name3', 'name4', 'name5']);
    expect(component.localState.categoricalView).toBe('range selector');

    component.switchCategoricalHistogramView('range selector');
    expect(component.localState.values).toStrictEqual(['name1', 'name2', 'name3', 'name4', 'name5']);
    expect(component.localState.categoricalView).toBe('range selector');
  });

  it('should replace current selected values', () => {
    const state: GenomicScoreState = {
      histogramType: 'categorical',
      score: 'score',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'range selector'
    };

    component.localState = state;
    component.replaceCategoricalValues(['val3', 'val4']);
    expect(component.localState.values).toStrictEqual(['val3', 'val4']);
  });

  it('should update range start and end', () => {
    component.selectedGenomicScore = new GenomicScore(
      'desc',
      'help',
      'score',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 7, 18, true, true)
    );

    const state: GenomicScoreState = {
      histogramType: 'continuous',
      score: 'score',
      rangeStart: 7,
      rangeEnd: 18,
      values: [],
      categoricalView: null
    };

    component.localState = state;
    component.updateRangeStart(10);
    component.updateRangeEnd(15);
    expect(component.localState.rangeStart).toBe(10);
    expect(component.localState.rangeEnd).toBe(15);
  });

  it('should get domain min and max', () => {
    component.selectedGenomicScore = new GenomicScore(
      'desc',
      'help',
      'score',
      new NumberHistogram([1, 2], [4, 5, 13, 20], 'larger1', 'smaller1', 7, 18, true, true)
    );

    expect(component.domainMin).toBe(4);
    expect(component.domainMax).toBe(20);
  });

  it('should set dropdown view as default when histogram bars count is more than the max', () => {
    const histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
      ],
      null,
      'large value descriptions',
      'small value descriptions',
      true,
      0,
      40
    );

    component.selectedGenomicScore = new GenomicScore(
      'desc',
      'help',
      'score',
      histogram
    );

    component.ngOnInit();

    expect(component.localState.categoricalView).toBe('dropdown selector');
  });

  it('should set dropdown view as default when histogram bars percent is more than the max', () => {
    const vals: {name: string, value: number}[] = range(30).map(v => {
      return {name: `name${v}`, value: v};
    });

    const histogram = new CategoricalHistogram(
      vals,
      null,
      'large value descriptions',
      'small value descriptions',
      true,
      0,
      null,
      100
    );

    component.selectedGenomicScore = new GenomicScore(
      'desc',
      'help',
      'score',
      histogram
    );

    component.ngOnInit();

    expect(component.localState.categoricalView).toBe('dropdown selector');
  });
});
