const { OAuthHandler } = require('@staticcms/netlify-oauth');
const handler = OAuthHandler();

exports.handler = handler;
