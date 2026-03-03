export const LOGIN_TRANSLATIONS = {
  pt: {
    title: "LOGIN DO AGENTE IA",
    email: "EMAIL",
    password: "SENHA",
    submit: "ENTRAR",
    theme: "TEMA",
    themeDark: "ESCURO",
    themeLight: "CLARO",
    connecting: "Conectando...",
    invalid: "Falha no login.",
  },
  en: {
    title: "IA AGENT LOGIN",
    email: "EMAIL",
    password: "PASSWORD",
    submit: "LOGIN",
    theme: "THEME",
    themeDark: "DARK",
    themeLight: "LIGHT",
    connecting: "Connecting...",
    invalid: "Login failed.",
  },
  es: {
    title: "LOGIN DEL AGENTE IA",
    email: "EMAIL",
    password: "CLAVE",
    submit: "ENTRAR",
    theme: "TEMA",
    themeDark: "OSCURO",
    themeLight: "CLARO",
    connecting: "Conectando...",
    invalid: "Error de inicio de sesion.",
  },
};

export function createLoginTranslator(language) {
  return function translate(key) {
    return LOGIN_TRANSLATIONS[language]?.[key] || LOGIN_TRANSLATIONS.pt[key] || key;
  };
}
