import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles block tests', () => {
  const page = new AutismGeneProfilesBlock();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
  const autismGeneProfilesSingleView = new AutismGeneProfilesSingleView();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should select multiple genes', () => {
    autismGeneProfilesTablePage.allTableRows.eq(1).click({ctrlKey:true});
    autismGeneProfilesTablePage.allTableRows.eq(3).click({ctrlKey:true});

    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► MYT1L, SPAST');

    autismGeneProfilesTablePage.allTableRows.eq(1).click({ctrlKey:true});

    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► SPAST');

  });

  it('should click dismiss gene compare button', () => {
    autismGeneProfilesTablePage.allTableRows.eq(3).click({ctrlKey:true});
    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► SPAST');

    autismGeneProfilesTablePage.allTableRows.eq(5).click({ctrlKey:true});
    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► SPAST, TBR1');

    autismGeneProfilesTablePage.legendDismissButton.click();
    autismGeneProfilesTablePage.legend.should('not.exist');
    autismGeneProfilesTablePage.legendCompareButton.should('not.exist');
    autismGeneProfilesTablePage.legendDismissButton.should('not.exist');
    autismGeneProfilesTablePage.legendSelectedGenes.should('not.exist');
  });

  it('should click compare genes button', () => {
    autismGeneProfilesTablePage.allTableRows.eq(1).click({ctrlKey:true});
    autismGeneProfilesTablePage.allTableRows.eq(3).click({ctrlKey:true});

    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► MYT1L, SPAST');

    autismGeneProfilesTablePage.legendCompareButton.click();
  });
});
