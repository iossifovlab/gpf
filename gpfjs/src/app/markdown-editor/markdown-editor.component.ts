import { Component, EventEmitter, HostListener, Input, OnChanges, Output } from '@angular/core';
import { EditorOption } from 'angular-markdown-editor';
import DOMPurify from 'dompurify';
import { MarkdownService } from 'ngx-markdown';

@Component({
  selector: 'gpf-markdown-editor',
  templateUrl: './markdown-editor.component.html',
  styleUrls: ['./markdown-editor.component.css']
})
export class MarkdownEditorComponent implements OnChanges {
  @Input() public initialMarkdown: string;
  @Input() public editable = true;

  @Output() public writeEvent = new EventEmitter<string>();

  public markdown: string;
  public editMode = false;
  public loading = true;

  public editorOptions: EditorOption = {
    autofocus: true,
    iconlibrary: 'fa',
    width: 1105,
    resize: 'both',
    fullscreen: {enable: false, icons: undefined},
    parser: (val: string) => {
      const sanitizedText = DOMPurify.sanitize(val.trim()) as string;
      return this.markdownService.parse(sanitizedText);
    }
  };

  public constructor(
    private markdownService: MarkdownService,
  ) { }

  @HostListener('keydown', ['$event']) public onKeyDown($event: KeyboardEvent): void {
    if ($event.ctrlKey && $event.code === 'Enter') {
      this.save();
    }
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
