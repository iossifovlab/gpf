export interface JqueryUIElement {
  autocomplete: (arg: object | string) => {bind: (value: string, func: () => void) => void};
  trigger: (trigger: string) => void;
  attr: (attr: string, value: string) => void;
  val: (value: string) => void;
  blur: () => void;
  keyup: (func: (event: {keyCode: number}) => void) => void;
}
