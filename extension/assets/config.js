export const defaultConfig = {
  // API key - Now loaded from cap_solver_api.txt file
  // The value here is only used as a fallback if the file cannot be read
  apiKey: 'CAP-B73C7B1CDD1B3B2DF298AD6555AF63C500021212E305B2FCA22B9C48EE1C4AF3',

  // Your Developer appId, Apply in dashboard's developer section
  appId: '',

  // Is the extension enabled by default or not
  useCapsolver: true,

  // Solve captcha manually
  manualSolving: false,

  // Captcha solved callback function name
  solvedCallback: 'captchaSolvedCallback',

  // Use proxy or not
  // If useProxy is true, then proxyType, hostOrIp, port, proxyLogin, proxyPassword are required
  useProxy: false,
  proxyType: 'http',
  hostOrIp: '',
  port: '',
  proxyLogin: '',
  proxyPassword: '',

  enabledForBlacklistControl: false, // Use blacklist control
  blackUrlList: [], // Blacklist URL list

  // Is captcha enabled by default or not
  enabledForRecaptcha: true,
  enabledForRecaptchaV3: true,
  enabledForImageToText: true,
  enabledForAwsCaptcha: true,
  enabledForCloudflare: true,

  // Task type: click or token
  reCaptchaMode: 'click',
  hCaptchaMode: 'click',

  // Delay before solving captcha
  reCaptchaDelayTime: 0,
  hCaptchaDelayTime: 0,
  textCaptchaDelayTime: 0,
  awsDelayTime: 0,

  // Number of repeated solutions after an error
  reCaptchaRepeatTimes: 10,
  reCaptcha3RepeatTimes: 10,
  hCaptchaRepeatTimes: 10,
  funCaptchaRepeatTimes: 10,
  textCaptchaRepeatTimes: 10,
  awsRepeatTimes: 10,

  // ReCaptcha V3 task type: ReCaptchaV3TaskProxyLess or ReCaptchaV3M1TaskProxyLess
  reCaptcha3TaskType: 'ReCaptchaV3TaskProxyLess',

  textCaptchaSourceAttribute: 'capsolver-image-to-text-source', // ImageToText source img's attribute name
  textCaptchaResultAttribute: 'capsolver-image-to-text-result', // ImageToText result element's attribute name

  textCaptchaModule: 'common', // ImageToText module
};
