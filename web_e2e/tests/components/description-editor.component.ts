import { Locator, Page } from '@playwright/test';

// Component object for the markdown description editor shared by the
// dataset description page (`gpf-dataset-description`) and the home page
// (`gpf-markdown-editor` inside `#edit-container`).
export class DescriptionEditor {
  public readonly datasetDescription: Locator;
  public readonly markdownEditor: Locator;
  public readonly editIcon: Locator;
  public readonly emptyDescription: Locator;
  public readonly editor: Locator;
  public readonly editorTextarea: Locator;
  public readonly markdownEditorTextarea: Locator;
  public readonly mdHeader: Locator;
  public readonly markdownParagraph: Locator;
  public readonly editContainerParagraph: Locator;

  // Editor action buttons (rendered as text).
  public readonly previewButton: Locator;
  public readonly saveButton: Locator;
  public readonly closeButton: Locator;

  public constructor(private readonly page: Page) {
    this.datasetDescription = page.locator('gpf-dataset-description');
    this.markdownEditor = page.locator('gpf-markdown-editor');
    this.editIcon = page.locator('#edit-icon');
    this.emptyDescription = page.locator('#empty-description');
    this.editor = page.locator('.editor');
    this.editorTextarea = page.locator('.editor textarea');
    this.markdownEditorTextarea = this.markdownEditor.locator('textarea');
    this.mdHeader = page.locator('.md-header');
    this.markdownParagraph = page.locator('markdown p');
    this.editContainerParagraph = page.locator('#edit-container p');

    this.previewButton = page.getByText('Preview');
    this.saveButton = page.getByText('Save');
    this.closeButton = page.getByText('Close');
  }
}
