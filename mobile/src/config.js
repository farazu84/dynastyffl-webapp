// For Expo Go on a physical device, use your machine's local IP instead of localhost.
// Run `ipconfig getifaddr en0` in your terminal to find it.
// Example: 'http://192.168.1.42:5000/v1'
const LOCAL_API = 'http://10.0.0.148:5000/v1';
const PROD_API  = 'https://d34t1k2xpw6h8v.cloudfront.net/v1';

const config = {
  API_BASE_URL: __DEV__ ? LOCAL_API : PROD_API,
};

export default config;
