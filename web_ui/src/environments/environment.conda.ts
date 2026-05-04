import versionInfo from '../../version.json';
const basePath = '/';

export const environment = {
  production: true,
  basePath: '',
  apiPath: basePath + 'api/v3/',
  imgPathPrefix: basePath + 'static/gpfjs/gpfjs/assets/',
  sentryTunnel: '',
  oauthClientId: 'gpfjs',
  version: versionInfo.version
};
