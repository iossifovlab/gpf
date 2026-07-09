import { Locator, Page } from '@playwright/test';
import { SelectStudiesModal } from './select-studies-modal.component';

// Component object for the `gpf-gene-sets` block. Two collection dropdowns
// are preserved from the original specs: `collectionSelect` (referenced by
// id in the Genotype browser gene-sets tab) and `collectionSelectForm`
// (referenced by class in the Gene browser / download flow).
export class GeneSets {
  public readonly root: Locator;
  public readonly collectionSelect: Locator;
  public readonly collectionSelectForm: Locator;
  public readonly searchInput: Locator;
  public readonly selectedValue: Locator;
  public readonly pleaseSelectHint: Locator;
  public readonly downloadLink: Locator;
  public readonly setsDropdownOptions: Locator;
  public readonly countSpan: Locator;
  public readonly alertDanger: Locator;
  public readonly searchBox: Locator;
  public readonly firstMatOption: Locator;
  public readonly selectStudiesModal: SelectStudiesModal;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-sets');
    this.collectionSelect = page.locator('select#selected-collection');
    this.collectionSelectForm = this.root.locator('select.form-control');
    this.searchInput = page.getByPlaceholder('Select or start typing to search');
    this.selectedValue = page.locator('span#selected-value');
    this.pleaseSelectHint = page.getByText('Please select a gene set.');
    this.downloadLink = this.root.getByRole('link', { name: 'Download' });
    this.setsDropdownOptions = page.locator('.sets-dropdown mat-option');
    this.countSpan = page.locator('span:has-text("Count:")');
    this.alertDanger = page.locator('.alert-danger');
    this.searchBox = page.locator('input#search-box');
    this.firstMatOption = page.locator('mat-option').first();
    this.selectStudiesModal = new SelectStudiesModal(page);
  }

  public setsDropdownOption(text: string): Locator {
    return this.setsDropdownOptions.filter({ hasText: text });
  }

  public option(name: string): Locator {
    return this.page.getByRole('option', { name });
  }

  public async selectCollection(collection: string): Promise<void> {
    await this.collectionSelect.selectOption(collection);
  }

  public async selectCollectionForm(collection: string | { label: string }): Promise<void> {
    await this.collectionSelectForm.selectOption(collection);
  }

  public async search(value: string): Promise<void> {
    await this.searchInput.click();
    await this.searchInput.focus();
    await this.page.keyboard.type(value);
  }
}
