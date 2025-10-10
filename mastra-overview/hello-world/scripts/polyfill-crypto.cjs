// Polyfill crypto for Node 18 compatibility
const { webcrypto } = require('node:crypto');
if (!globalThis.crypto) {
  globalThis.crypto = webcrypto;
}
