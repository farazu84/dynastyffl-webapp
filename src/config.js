// API Configuration
const config = {
  // Use environment variable if available, otherwise use CloudFront for production
  API_BASE_URL: process.env.REACT_APP_API_URL || 'https://d34t1k2xpw6h8v.cloudfront.net',
};

export default config;
