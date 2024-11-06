import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { Observable } from 'rxjs';
import { of } from 'rxjs/internal/observable/of';
import { GeneScores, NumberHistogram } from './gene-scores';
import { GeneScoresComponent } from './gene-scores.component';
import { GeneScoresService } from './gene-scores.service';
import { geneScoresReducer } from './gene-scores.state';
import { Store, StoreModule } from '@ngrx/store';

class MockGeneScoresService {
  public provide = true;
  public getGeneScores(): Observable<GeneScores[]> {
    if (this.provide) {
      return of([
        new GeneScores(
          'desc1',
          'help1',
          'score1',
          new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 7, 8, true, true),
        ),
        new GeneScores(
          'desc2',
          'help2',
          'score2',
          new NumberHistogram([11, 12], [14, 15], 'larger2', 'smaller2', 17, 88, true, true),
        )
      ]);
    } else {
      return of([] as GeneScores[]);
    }
  }
}
describe('GeneScoresComponent', () => {
  let component: GeneScoresComponent;
  let fixture: ComponentFixture<GeneScoresComponent>;
  let mockGeneScoresService: MockGeneScoresService;
  let store: Store;

  beforeEach(() => {
    mockGeneScoresService = new MockGeneScoresService();

    TestBed.configureTestingModule({
      imports: [
        StoreModule.forRoot({geneScores: geneScoresReducer}), HttpClientTestingModule, NgbNavModule
      ],
      declarations: [GeneScoresComponent],
      providers: [{provide: GeneScoresService, useValue: mockGeneScoresService}, ConfigService],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of({score: 'score1'}));

    fixture = TestBed.createComponent(GeneScoresComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should test setting gene scores', () => {
    fixture.detectChanges();
    expect(component.selectedGeneScores.score).toBe('score1');
  });

  it('should test empty gene scores', () => {
    mockGeneScoresService.provide = false;
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('div > div.form-block > div.card > ul > li > span'))).toBeTruthy();
    expect(fixture.debugElement.query(By.css('div > div#gene-scores-panel'))).not.toBeTruthy();
  });
});

