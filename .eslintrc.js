module.exports = {
  env: {
    browser: true,
    commonjs: true,
    es2021: true,
    node: true,
  },
  extends: 'airbnb-base',
  overrides: [
    {
      env: {
        node: true,
      },
      files: [
        '.eslintrc.{js,cjs}',
      ],
      parserOptions: {
        sourceType: 'script',
      },
    },
  ],
  parserOptions: {
    ecmaVersion: 'latest',
  },
  rules: {
    'no-console': 'off', // Disable the 'no-console' rule
    'no-shadow': 'off', // Disable the 'no-shadow' rule
    'no-undef': 'off', // Disable the 'no-undef' rule
    'func-names': 'off', // Disable the 'func-names' rule
  },
};
