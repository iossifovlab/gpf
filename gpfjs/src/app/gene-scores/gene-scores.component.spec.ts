import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { Observable } from 'rxjs';
import { of } from 'rxjs/internal/observable/of';
import { GeneScores } from './gene-scores';
import { GeneScoresComponent } from './gene-scores.component';
import { GeneScoresService } from './gene-scores.service';
import { GeneScoresState } from './gene-scores.state';

class MockGeneScoresService {
  public provide = true;
  public getGeneScores(geneScoresIds?: string): Observable<GeneScores[]> {
    if (this.provide) {
      return of([new GeneScores([1, 2], 'score3', [4, 5], 'desc6', [7, 8], 'xScale9', 'yScale10'),
        new GeneScores([11, 12], 'score13', [14, 15], 'desc16', [17, 18], 'xScale19', 'yScale20')
      ]);
    } else {
      return of([] as GeneScores[]);
    }
  }
}
describe('GeneScoresComponent', () => {
  let component: GeneScoresComponent;
  let fixture: ComponentFixture<GeneScoresComponent>;
  const mockGeneScoresService: MockGeneScoresService = new MockGeneScoresService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        NgxsModule.forRoot([GeneScoresState], {developmentMode: true}), HttpClientTestingModule, NgbNavModule
      ],
      declarations: [GeneScoresComponent],
      providers: [{provide: GeneScoresService, useValue: mockGeneScoresService}, ConfigService],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
  }));

  beforeEach(() => {
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
    component.selectedGeneScores = undefined as any;
    component.ngOnInit();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(fixture.debugElement.query(By.css('div > div.form-block > div.card > ul > li > span'))).toBeTruthy();
      expect(fixture.debugElement.query(By.css('div > div#gene-scores-panel'))).not.toBeTruthy();
    });
  });
});

