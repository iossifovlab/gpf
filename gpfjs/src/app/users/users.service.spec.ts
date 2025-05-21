import { APP_BASE_HREF } from '@angular/common';
import { HttpClient, HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from './users.service';
import { AuthService } from 'app/auth.service';
import { lastValueFrom, of, take, throwError } from 'rxjs';
import { User } from './users';
import { FederationCredential } from 'app/federation-credentials/federation-credentials';

describe('UsersService', () => {
  let service: UsersService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ConfigService,
        UsersService,
        AuthService,
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      imports: [
        RouterModule.forRoot([])
      ]
    });
    service = TestBed.inject(UsersService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should logout user', async() => {
    service.isLoggingOut = false;

    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of({}));

    jest.spyOn(service['cookieService'], 'get').mockReturnValue('tokenMock');
    jest.spyOn(service['locationStrategy'], 'getBaseHref').mockReturnValue('/mockHref');

    const revokeAccessTokenSpy = jest.spyOn(service['authService'], 'revokeAccessToken');
    const clearTokensSpy = jest.spyOn(service['authService'], 'clearTokens');

    const logoutResult = service.logout();
    expect(service.isLoggingOut).toBe(true);

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['logoutUrl'],
      {},
      { headers: { 'X-CSRFToken': 'tokenMock' }, withCredentials: true}
    );

    const res = await lastValueFrom(logoutResult.pipe(take(1)));
    expect(res).toStrictEqual({});
    expect(revokeAccessTokenSpy).toHaveBeenCalledWith();
    expect(clearTokensSpy).toHaveBeenCalledWith();
  });

  it('should get stored user info', () => {
    const userInfo = {
      email: 'user@email.com',
      isAdministrator: true,
      loggedIn: true
    };
    service['lastUserInfo'] = userInfo;
    expect(service.cachedUserInfo()).toStrictEqual(userInfo);
  });

  it('should get info of the current user', async() => {
    const userInfo = {
      email: 'user@email.com',
      isAdministrator: true,
      loggedIn: true
    };

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(userInfo));

    const getResult = service.getUserInfo();

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['userInfoUrl'],
      { withCredentials: true}
    );

    const res = await lastValueFrom(getResult.pipe(take(1)));
    expect(res).toBe(userInfo);
    expect(service['lastUserInfo']).toStrictEqual(userInfo);
  });

  it('should reset password', () => {
    jest.spyOn(service['cookieService'], 'get').mockReturnValue('tokenMock');

    // eslint-disable-next-line jest/prefer-spy-on
    global.fetch = jest.fn();
    const fetchSpy = jest.spyOn(global, 'fetch');
    service.resetPassword('user@email.com');
    expect(fetchSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['resetPasswordUrl'],
      {
        body: '{"email":"user@email.com"}',
        headers: {
          'X-CSRFToken': 'tokenMock',
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        method: 'POST'
      }
    );
  });

  it('should get all users', async() => {
    const users = [
      new User(1, 'username1', 'user1@email.com', [], true, []),
      new User(2, 'username2', 'user2@email.com', [], true, []),
      new User(3, 'username3', 'user3@email.com', [], true, [])
    ];

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(users));

    const getResult = service.getAllUsers();

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'],
      { withCredentials: true }
    );

    const res = await lastValueFrom(getResult.pipe(take(1)));
    expect(res).toStrictEqual(users);
  });

  it('should get user by id', async() => {
    const user = new User(1, 'username1', 'user1@email.com', [], true, []);

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(user));

    const getResult = service.getUser(1);

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'] + '/1',
      { withCredentials: true }
    );

    const res = await lastValueFrom(getResult.pipe(take(1)));
    expect(res).toStrictEqual(user);
  });

  it('should update user', async() => {
    const user = new User(1, 'username1', 'user1@email.com', [], true, []);

    const dto = {
      id: user.id,
      name: user.name,
      groups: user.groups,
      hasPassword: user.hasPassword,
    };

    jest.spyOn(service['cookieService'], 'get').mockReturnValue('tokenMock');

    const httpPutSpy = jest.spyOn(HttpClient.prototype, 'put');
    httpPutSpy.mockReturnValue(of(user));

    const putResult = service.updateUser(user);

    expect(httpPutSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'] + '/1',
      dto,
      { headers: { 'X-CSRFToken': 'tokenMock' }, withCredentials: true }
    );

    const res = await lastValueFrom(putResult.pipe(take(1)));
    expect(res).toStrictEqual(user);


    service.updateUser(new User(null, 'name', 'email', [], false, []));
    expect(httpPutSpy).not.toHaveBeenCalledWith();
  });

  it('should create user', async() => {
    const user = new User(10, 'newUser', 'newUser@email.com', [], true, []);

    jest.spyOn(service['cookieService'], 'get').mockReturnValue('tokenMock');

    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(user));

    user.id = null;
    const putResult = service.createUser(user);

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'],
      user,
      { headers: { 'X-CSRFToken': 'tokenMock' }, withCredentials: true }
    );

    user.id = 10;
    const res = await lastValueFrom(putResult.pipe(take(1)));
    expect(res).toStrictEqual(user);
  });

  it('should throw error when creating user', () => {
    const user = new User(10, 'newUser', 'newUser@email.com', [], true, []);

    jest.spyOn(service['cookieService'], 'get').mockReturnValue('tokenMock');

    const httpError = new HttpErrorResponse({
      error: 'no such user',
      status: 404,
      statusText: 'status fail',
      url: service['usersUrl']
    });

    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(throwError(() => httpError));

    const postResult = service.createUser(user);

    // eslint-disable-next-line jest/valid-expect
    expect(() => lastValueFrom(postResult.pipe(take(1))))
      .rejects.toThrow('Http failure response for users: 404 status fail');
  });

  it('should delete user', async() => {
    const user = new User(10, 'user', 'user@email.com', [], true, []);

    const httpDeleteSpy = jest.spyOn(HttpClient.prototype, 'delete');
    httpDeleteSpy.mockReturnValue(of(user));

    const deleteResult = service.deleteUser(user);

    expect(httpDeleteSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'] + '/10',
      { withCredentials: true }
    );

    const res = await lastValueFrom(deleteResult.pipe(take(1)));
    expect(res).toStrictEqual(user);

    user.id = null;
    service.deleteUser(user);
    expect(httpDeleteSpy).not.toHaveBeenCalledWith();
  });

  it('should remove user from group', async() => {
    const user = new User(10, 'user', 'user@email.com', ['group1', 'group2'], true, []);
    const updatedUser = new User(10, 'user', 'user@email.com', ['group1'], true, []);
    const updateUserSpy = jest.spyOn(service, 'updateUser').mockReturnValue(of(updatedUser));

    const removeResult = service.removeUserGroup(user, 'group2');

    const res = await lastValueFrom(removeResult.pipe(take(1)));
    expect(res).toStrictEqual(updatedUser);
    expect(updateUserSpy).toHaveBeenCalledWith(updatedUser);
  });

  it('should load users when searching and loading pages', async() => {
    const users = [
      new User(1, 'username1', 'user1@email.com', ['group1'], true, [
        {datasetId: 'dataset_1', datasetName: 'dataset'},
        {datasetId: 'dataset_2', datasetName: 'dataset'},
      ]),
    ];

    const usersResult = [
      new User(1, 'username1', 'user1@email.com', ['group1'], true, [
        {datasetId: 'dataset_1', datasetName: 'dataset(dataset_1)'},
        {datasetId: 'dataset_2', datasetName: 'dataset(dataset_2)'},
      ]),
    ];

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(users));

    const getResult = service.getUsers(1, 'user1');

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'] + '?page=1&search=user1',
      { withCredentials: true }
    );

    const res = await lastValueFrom(getResult.pipe(take(1)));
    expect(res).toStrictEqual(usersResult);
  });

  it('should get empty response when getting users', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(null));

    const getResultEmpty = service.getUsers(1, 'user1');
    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['usersUrl'] + '?page=1&search=user1',
      { withCredentials: true }
    );

    const resEmpty = await lastValueFrom(getResultEmpty.pipe(take(1)));
    expect(resEmpty).toStrictEqual([]);
  });

  it('should get federation credentials', async() => {
    const credentialsMock = [{name: 'cred1'}, {name: 'cred2'}, {name: 'cred3'}];

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(credentialsMock));

    const getResult = service.getFederationCredentials();

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + 'users/federation_credentials',
      { withCredentials: true }
    );

    const res = await lastValueFrom(getResult.pipe(take(1)));
    expect(res).toStrictEqual([
      new FederationCredential('cred1'),
      new FederationCredential('cred2'),
      new FederationCredential('cred3'),
    ]);
  });

  it('should create federation credentials', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of({
      client_id: 'mockClientId',
      client_secret: 'mockClientSecret',
    }));

    const postResult = service.createFederationCredentials('mockCredentialName');
    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + 'users/federation_credentials',
      { name: 'mockCredentialName' },
      { withCredentials: true }
    );

    const res = await lastValueFrom(postResult.pipe(take(1)));
    expect(res.client_id).toBe('mockClientId');
    expect(res.client_secret).toBe('mockClientSecret');
  });

  it('should update federation credentials', async() => {
    const httpPutSpy = jest.spyOn(HttpClient.prototype, 'put');
    httpPutSpy.mockReturnValue(of({new_name: 'newCredName'}));

    const putResult = service.updateFederationCredentials('oldCredName', 'newCredName');

    expect(httpPutSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + 'users/federation_credentials',
      { name: 'oldCredName', new_name: 'newCredName' },
      { withCredentials: true }
    );

    const res = await lastValueFrom(putResult.pipe(take(1)));
    expect(res).toBe('newCredName');
  });

  it('should delete federation credentials', async() => {
    const httpDeleteSpy = jest.spyOn(HttpClient.prototype, 'delete');
    httpDeleteSpy.mockReturnValue(of({}));

    const deleteResult = service.deleteFederationCredentials('credentialName');

    expect(httpDeleteSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + 'users/federation_credentials',
      { withCredentials: true, body: { name: 'credentialName' } }
    );

    const res = await lastValueFrom(deleteResult.pipe(take(1)));
    expect(res).toStrictEqual({});
  });
});