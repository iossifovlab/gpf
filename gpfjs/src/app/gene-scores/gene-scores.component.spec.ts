import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { Observable } from 'rxjs';
import { of } from 'rxjs/internal/observable/of';
import { GeneScores } from './gene-scores';
import { GeneScoresComponent } from './gene-scores.component';
import { GeneScoresService } from './gene-scores.service';
import { geneScoresReducer } from './gene-scores.state';
import { StoreModule } from '@ngrx/store';

class MockGeneScoresService {
  public provide = true;
  public getGeneScores(): Observable<GeneScores[]> {
    if (this.provide) {
      return of([
        new GeneScores(
          [1, 2], [4, 5], 'desc1', 'help1', 'larger1', 'smaller1', 'score31', [7, 8], 'xScale1', 'yScale1'
        ),
        new GeneScores(
          [11, 12], [14, 15], 'desc2', 'help2', 'larger2', 'smaller2', 'score2', [17, 18], 'xScale2', 'yScale2'
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

    fixture = TestBed.createComponent(GeneScoresComponent);
    component = fixture.componentInstance;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should test empty gene sets', () => {
    expect(fixture.debugElement.query(By.css('div > div#gene-scores-panel'))).toBeTruthy();
    mockGeneScoresService.provide = false;
    component.selectedGeneScores = undefined;
    component.ngOnInit();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('div > div.form-block > div.card > ul > li > span'))).toBeTruthy();
    expect(fixture.debugElement.query(By.css('div > div#gene-scores-panel'))).not.toBeTruthy();
  });
});

