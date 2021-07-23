/* tslint:disable:no-unused-variable */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';

import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { GenesBlockComponent } from './genes-block.component';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSymbolsComponent, GenesBlockComponent],
      imports: [NgbModule, NgxsModule.forRoot([])],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce(f) {
        return of({geneSymbols: ['value1', 'value2']});
      },
      dispatch(set) {}
    } as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
