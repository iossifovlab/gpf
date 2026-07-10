import { Page } from '@playwright/test';
import { Header } from '../components/header.component';
import { GeneProfilesBlock } from '../components/gene-profiles-block.component';
import { GeneProfilesTable } from '../components/gene-profiles-table.component';
import { GeneProfilesSingleView } from '../components/gene-profiles-single-view.component';

// Page object for the Gene Profiles view, composing the block, table
// and single-view component objects.
export class GeneProfilesPage {
  public readonly header: Header;
  public readonly block: GeneProfilesBlock;
  public readonly table: GeneProfilesTable;
  public readonly singleView: GeneProfilesSingleView;

  public constructor(private readonly page: Page) {
    this.header = new Header(page);
    this.block = new GeneProfilesBlock(page);
    this.table = new GeneProfilesTable(page);
    this.singleView = new GeneProfilesSingleView(page);
  }

  // Opens Gene Profiles from the header navigation.
  public async open(): Promise<void> {
    await this.header.navLink('Gene Profiles').click();
  }
}
