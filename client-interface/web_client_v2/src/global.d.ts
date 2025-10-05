declare module '*.css'

// React JSX types
declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}
