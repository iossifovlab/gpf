import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NgbModal, NgbModalRef, NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { Observable } from 'rxjs';
import { of } from 'rxjs/internal/observable/of';
import { GeneScores } from './gene-scores';
import { GeneScoresComponent } from './gene-scores.component';
import { GeneScoresService } from './gene-scores.service';
import { GeneScoresState } from './gene-scores.state';
import { PopupComponent } from 'app/popup/popup.component';

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
  let modalService: NgbModal;
  let modalRef: NgbModalRef;

  beforeEach(() => {
    mockGeneScoresService = new MockGeneScoresService();

    TestBed.configureTestingModule({
      imports: [
        NgxsModule.forRoot([GeneScoresState], {developmentMode: true}), HttpClientTestingModule, NgbNavModule
      ],
      declarations: [GeneScoresComponent],
      providers: [{provide: GeneScoresService, useValue: mockGeneScoresService}, ConfigService],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    modalService = TestBed.inject(NgbModal);
    modalRef = modalService.open(PopupComponent);

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

  it('should show help', () => {
    jest.spyOn(modalService, 'open').mockReturnValue(modalRef);
    component.showHelp();
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg',
      centered: true
    });
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg',
      centered: true
    });
    expect((modalRef.componentInstance as PopupComponent).data).toBe('help1');

    modalRef.close();
  });
});

