// API Configuration
const config = {
  // Use environment variable if available, otherwise use CloudFront for production
  API_BASE_URL: process.env.REACT_APP_API_URL 
    ? `${process.env.REACT_APP_API_URL}/v1`  // Add /v1 to local development URL
    : 'https://d34t1k2xpw6h8v.cloudfront.net/v1', // CloudFront already has /v1
};

export default config;
