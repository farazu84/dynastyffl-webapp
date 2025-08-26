// API Configuration
const config = {
  // Use environment variable if available, otherwise use production API
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://dynasty-api-prod-v2.eba-3xm8xpvu.us-west-2.elasticbeanstalk.com',
};

export default config;
