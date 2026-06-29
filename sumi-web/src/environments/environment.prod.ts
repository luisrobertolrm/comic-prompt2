// Deriva o prefixo do <base href> gravado no build (--base-href).
// Raiz ('/') => apiUrl ''; sub-path ('/sumi/') => apiUrl '/sumi'.
const baseHref = document.querySelector('base')?.getAttribute('href') ?? '/';

export const environment = {
  production: true,
  apiUrl: baseHref.replace(/\/$/, ''),
};
