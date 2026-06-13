// For Expo Go on a physical device, use your machine's local IP instead of localhost.
// Run `ipconfig getifaddr en0` in your terminal to find it.
// Your phone must be on the same WiFi network as this machine.
const LOCAL_API = 'http://10.0.0.148:5000/v1';
const PROD_API  = 'https://d34t1k2xpw6h8v.cloudfront.net/v1';

// Flip to false to hit the production API during development
const USE_LOCAL = true;

const config = {
  API_BASE_URL: __DEV__ && USE_LOCAL ? LOCAL_API : PROD_API,
};

export default config;
