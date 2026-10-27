import versionInfo from '../../version.json';
const basePath = '';

export const environment = {
  production: true,
  basePath: basePath,
  apiPath: basePath + 'api/v3/',
  imgPathPrefix: 'assets/',
  oauthClientId: 'gpfjs',
  version: versionInfo.version
};
