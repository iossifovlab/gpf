import { AutismGeneProfilesBlockPage } from 'cypress/elements/autism-gene-profiles-block-page';
import { GeneProfilesTablePage } from 'cypress/elements/autism-gene-profiles-table-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles block tests', () => {
  const page = new AutismGeneProfilesBlockPage();
  const GeneProfilesTablePagePage = new GeneProfilesTablePage();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome(false);
    page.navigateToSidenavPage(sidenavPageLinks.geneProfiles);
  });

  it('should display gene profiles table', () => {
    GeneProfilesTablePagePage.window.should('be.visible');
  });

  it('should display the keybind icon', () => {
    page.keybindIcon.should('be.visible');
  });

  it('should mouseover the keybind icon to show the keybind tool tip and then mouseout to hide it', () => {
    page.keybindTooltip.should('not.exist');

    page.keybindIcon.trigger('mouseover');
    page.keybindTooltip.should('be.visible');

    page.keybindIcon.trigger('mouseout');
    page.keybindTooltip.should('not.exist');
  });
});
