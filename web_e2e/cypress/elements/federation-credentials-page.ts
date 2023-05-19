import { BasePage } from './utils';

export class FederationCredentialsPage extends BasePage {
  public get federationTab(): element {
    return cy.get('a').contains('Federation tokens');
  }

  public get federationCredentials(): element {
    return cy.get('gpf-federation-credentials');
  }

  public get newCredentialInput(): element {
    return cy.get('#credential-name-box');
  }

  public get createCredentialButton(): element {
    return cy.get('#create-credential-button');
  }

  public get credentialsModal(): element {
    return cy.get('.credential-modal');
  }

  public get copyCredentialsButton(): element {
    return this.credentialsModal.find('#copy-credentials-button');
  }

  public get credentials(): element {
    return this.credentialsModal.find('#credential-modal-content');
  }

  public credentialNameCell(name: string): element {
    return cy.get(`div[id="${name}-name-cell"]`);
  }

  public credentialClientIdCell(name: string): element {
    return cy.get(`div[id="${name}-id-cell"]`);
  }

  public credentialClientSecretCell(name: string): element {
    return cy.get(`div[id="${name}-secret-cell"]`);
  }

  public credentialActionsCell(name: string): element {
    return cy.get(`div[id="${name}-actions-cell"]`);
  }

  public credentialDeleteButton(name: string): element {
    return this.credentialActionsCell(name).find('button[title="Delete credential"]');
  }

  public get deleteCredentialConfirmButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Delete');
  }

  public get existingNameError(): element {
    return cy.get('div').contains('Credential with such name already exists!');
  }

  public get InvalidNameError(): element {
    return cy.get('div').contains('Credential names must be at least 3 symbols long.');
  }
}
