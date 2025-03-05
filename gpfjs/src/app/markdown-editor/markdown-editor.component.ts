import { Component, EventEmitter, HostListener, Input, OnChanges, OnInit, Output } from '@angular/core';
import { EditorOption } from 'angular-markdown-editor';
import { UsersService } from 'app/users/users.service';
import { MarkdownService } from 'ngx-markdown';

@Component({
  selector: 'gpf-markdown-editor',
  templateUrl: './markdown-editor.component.html',
  styleUrls: ['./markdown-editor.component.css']
})
export class MarkdownEditorComponent implements OnInit, OnChanges {
  @Input() public initialMarkdown: string;
  @Input() public editable = true;

  @Output() public writeEvent = new EventEmitter<string>();

  public markdown: string;
  public editMode = false;
  public loading = true;
  public isUserAdmin = false;

  public editorOptions: EditorOption = {
    autofocus: true,
    iconlibrary: 'fa',
    width: 1105,
    resize: 'both',
    fullscreen: {enable: false, icons: undefined},
    parser: (val: string) => {
      return this.markdownService.parse(val.trim()) as string;
    }
  };

  public constructor(
    private markdownService: MarkdownService,
    private usersService: UsersService,
  ) { }

  @HostListener('keydown', ['$event']) public onKeyDown($event: KeyboardEvent): void {
    if ($event.ctrlKey && $event.code === 'Enter') {
      this.save();
    }
  }

  public ngOnInit(): void {
    this.isUserAdmin = this.usersService.cachedUserInfo().isAdministrator;
  }

  public ngOnChanges(): void {
    this.markdown = this.initialMarkdown;
  }

  public close(): void {
    this.editMode = false;
    if (this.markdown !== this.initialMarkdown) {
      this.markdown = this.initialMarkdown;
    }
  }

  public togglePreview(): void {
    const previewButton = document.querySelector('[title="Preview"]');
    if (this.markdown.length !== 0) {
      previewButton.removeAttribute('disabled');
    } else {
      previewButton.setAttribute('disabled', '');
    }
  }

  public disablePreviewOnLoad(toDisable: boolean): void {
    if (toDisable) {
      const previewButton = document.querySelector('[title="Preview"]');
      previewButton.setAttribute('disabled', '');
    }
  }

  public save(): void {
    this.loading = true;
    this.editMode = false;
    if (this.markdown !== this.initialMarkdown) {
      this.writeEvent.emit(this.markdown);
      this.initialMarkdown = this.markdown;
    }
  }
}
