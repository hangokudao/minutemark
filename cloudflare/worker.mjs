const ORIGIN_HOST = "minutemark-2u3l25uhba-du.a.run.app";

export default {
  fetch(request) {
    const originUrl = new URL(request.url);
    originUrl.protocol = "https:";
    originUrl.hostname = ORIGIN_HOST;
    originUrl.port = "";

    return fetch(new Request(originUrl, request));
  },
};
