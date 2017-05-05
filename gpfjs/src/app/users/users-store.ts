export const USER_LOGIN = 'USER_LOGIN';
export const USER_LOGOUT = 'USER_LOGOUT';

export interface UsersState {
  loggedIn: boolean;
};

export function usersReducer(
  state: UsersState = null,
  action
): UsersState {

  switch (action.type) {
    case USER_LOGIN:
      return { loggedIn: true }
    case USER_LOGOUT:
      return { loggedIn: false }
    default:
      return state;
  }
};
