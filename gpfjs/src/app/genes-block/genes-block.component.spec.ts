/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { GenesBlockComponent } from './genes-block.component';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GenesBlockComponent],
      imports: [
        NgbModule,
      ],
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
