import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MarkdownEditorComponent } from './markdown-editor.component';
import { MarkdownModule, MarkdownService } from 'ngx-markdown';
import { UsersService } from 'app/users/users.service';
import { HttpClient, HttpHandler } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { StoreModule } from '@ngrx/store';
import { APP_BASE_HREF } from '@angular/common';
import { UserInfo } from 'app/users/users';

class UsersServiceMock {
  public cachedUserInfo(): UserInfo {
    return {
      email: "testmail@mail.com",
      isAdministrator: true,
      loggedIn: true,
    }
  }
}

describe('MarkdownEditorComponent', () => {
  let component: MarkdownEditorComponent;
  let fixture: ComponentFixture<MarkdownEditorComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [MarkdownEditorComponent],
      providers: [
        MarkdownService,
        { provide: UsersService, useClass: UsersServiceMock },
        HttpClient,
        HttpHandler,
        ConfigService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [MarkdownModule.forRoot(), StoreModule.forRoot({})]
    }).compileComponents();

    fixture = TestBed.createComponent(MarkdownEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set markdown', () => {
    component.initialMarkdown = 'initial markdown text';
    component.markdown = 'current markdown';
    component.ngOnChanges();
    expect(component.markdown).toBe(component.initialMarkdown);
  });

  it('should close editor and change markdown to initial markdown', () => {
    component.initialMarkdown = 'initial markdown text';
    component.markdown = 'current markdown';
    component.editMode = true;
    component.close();
    expect(component.editMode).toBe(false);
    expect(component.markdown).toBe(component.initialMarkdown);
  });
});
