function meroHubModule(api) {
  var symbols = [
    "EkiohMediaControl", "EkiohStreamInfo", "EkiohAudioStreamInfo",
    "EkiohSubtitleStreamInfo", "SVGVisualMediaElement", "media"
  ];
  function names(value) {
    try { return Object.getOwnPropertyNames(value).join("|").substr(0, 1800); }
    catch (error) { return "error:" + String(error); }
  }
  function inspect(name) {
    var value, prototype;
    try { value = window[name]; }
    catch (error) { api.report("media020." + name + ".access", String(error)); return; }
    api.report("media020." + name + ".type", typeof value);
    if (value === undefined || value === null) return;
    api.report("media020." + name + ".own", names(value));
    if (typeof value == "function") {
      api.report("media020." + name + ".arity", value.length);
      try { api.report("media020." + name + ".signature", String(value).substr(0, 350)); }
      catch (error2) { api.report("media020." + name + ".signature.error", String(error2)); }
    }
    try { prototype = value.prototype; }
    catch (error3) { api.report("media020." + name + ".prototype.error", String(error3)); return; }
    if (prototype) api.report("media020." + name + ".prototype", names(prototype));
  }
  function descriptor(label, object, key) {
    try {
      var item = Object.getOwnPropertyDescriptor(object, key);
      api.report("media020." + label + "." + key + ".descriptor",
        item ? "get=" + typeof item.get + ",set=" + typeof item.set +
          ",value=" + typeof item.value + ",writable=" + item.writable : "absent");
    } catch (error) { api.report("media020." + label + "." + key + ".error", String(error)); }
  }
  api.setStatus("MEDIA API INSPECTION");
  api.setDetail("Read-only Ekioh media-control reflection");
  api.report("media020.version", "passive-v1");
  for (var i = 0; i < symbols.length; i++) inspect(symbols[i]);
  api.report("media020.complete", "passive");
  var globalControl = window.EkiohMediaControl;
  if (globalControl) {
    var fields = ["videoStreams", "videoStream", "audioStreams", "audioStream", "displayTeletext"];
    for (var j = 0; j < fields.length; j++) {
      try {
        var field = globalControl[fields[j]];
        api.report("media020.global." + fields[j] + ".type", typeof field);
        if (field !== undefined && field !== null)
          api.report("media020.global." + fields[j] + ".own", names(field));
      } catch (error4) { api.report("media020.global." + fields[j] + ".error", String(error4)); }
    }
  }
  try {
    var video = document.createElementNS("http://www.w3.org/2000/svg", "video");
    api.report("media020.video.detached.type", typeof video);
    api.report("media020.video.detached.own", names(video));
    api.report("media020.video.detached.control.type", typeof video.ekiohControl);
    if (video.ekiohControl) api.report("media020.video.detached.control.own", names(video.ekiohControl));
    video.setAttribute("x", "0");
    video.setAttribute("y", "0");
    video.setAttribute("width", "0");
    video.setAttribute("height", "0");
    document.documentElement.appendChild(video);
    api.report("media020.video.attached.control.type", typeof video.ekiohControl);
    if (video.ekiohControl) api.report("media020.video.attached.control.own", names(video.ekiohControl));
    api.report("media020.video.currentTime.type", typeof video.currentTime);
    api.report("media020.video.setSpeed.type", typeof video.setSpeed);
    var parent = Object.getPrototypeOf(video);
    api.report("media020.video.parent.own", names(parent));
    api.report("media020.video.parent.isGlobal", parent === window.SVGVisualMediaElement);
    descriptor("video.parent", parent, "ekiohControl");
    descriptor("video.parent", parent, "setSpeed");
  } catch (error5) { api.report("media020.video.error", String(error5)); }
  descriptor("global.prototype", window.EkiohMediaControl, "videoStream");
  descriptor("global.prototype", window.EkiohMediaControl, "videoStreams");
  descriptor("global.prototype", window.SVGVisualMediaElement, "ekiohControl");
  api.report("media020.detail.complete", "descriptor-v3-no-playback");
  try {
    var libraryRequest = new XMLHttpRequest();
    libraryRequest.onreadystatechange = function () {
      if (libraryRequest.readyState == 4)
        api.report("media020.direct.library", "status=" + libraryRequest.status +
          ",bytes=" + libraryRequest.responseText.length);
    };
    libraryRequest.open("GET", "http://192.168.1.97:39019/api/videos", true);
    libraryRequest.send(null);
  } catch (libraryError) { api.report("media020.direct.library.error", String(libraryError)); }
  try {
    var testVideo = document.createElementNS("http://www.w3.org/2000/svg", "video");
    testVideo.setAttribute("x", "320");
    testVideo.setAttribute("y", "180");
    testVideo.setAttribute("width", "640");
    testVideo.setAttribute("height", "360");
    testVideo.setAttribute("type", "video/mp4");
    testVideo.setAttribute("begin", "indefinite");
    testVideo.setAttributeNS("http://www.w3.org/1999/xlink", "href",
      "http://192.168.1.97:39019/video/ec4262376255b0d7");
    testVideo.addEventListener("beginEvent", function () { api.report("media020.direct.beginEvent", "received"); }, false);
    testVideo.addEventListener("endEvent", function () { api.report("media020.direct.endEvent", "received"); }, false);
    testVideo.addEventListener("error", function () { api.report("media020.direct.errorEvent", "received"); }, false);
    document.documentElement.appendChild(testVideo);
    api.report("media020.direct.control.type", typeof testVideo.ekiohControl);
    if (testVideo.ekiohControl) {
      api.report("media020.direct.control.own", names(testVideo.ekiohControl));
      api.report("media020.direct.control.parent", names(Object.getPrototypeOf(testVideo.ekiohControl)));
      var controlFields = ["videoStreams", "videoStream", "audioStreams", "audioStream", "displayTeletext"];
      for (var k = 0; k < controlFields.length; k++) {
        try { api.report("media020.direct.control." + controlFields[k] + ".type",
          typeof testVideo.ekiohControl[controlFields[k]]); }
        catch (controlError) { api.report("media020.direct.control." + controlFields[k] + ".error", String(controlError)); }
      }
    }
    api.report("media020.direct.begin.type", typeof testVideo.beginElement);
    if (typeof testVideo.beginElement == "function") testVideo.beginElement();
    setTimeout(function () {
      api.report("media020.direct.after10.currentTime", testVideo.currentTime);
      api.report("media020.direct.after10.control.type", typeof testVideo.ekiohControl);
    }, 10000);
  } catch (videoError) { api.report("media020.direct.error", String(videoError)); }
  try {
    var sameOriginVideo = document.createElementNS("http://www.w3.org/2000/svg", "video");
    sameOriginVideo.setAttribute("x", "0");
    sameOriginVideo.setAttribute("y", "0");
    sameOriginVideo.setAttribute("width", "1");
    sameOriginVideo.setAttribute("height", "1");
    sameOriginVideo.setAttribute("type", "video/mp4");
    sameOriginVideo.setAttribute("begin", "indefinite");
    sameOriginVideo.setAttributeNS("http://www.w3.org/1999/xlink", "href",
      "http://191.32.31.251/probe.svg?media020=same-origin-v6");
    document.documentElement.appendChild(sameOriginVideo);
    if (typeof sameOriginVideo.beginElement == "function") sameOriginVideo.beginElement();
    api.report("media020.sameOrigin.begin", "called");
    setTimeout(function () { api.report("media020.sameOrigin.after5.currentTime", sameOriginVideo.currentTime); }, 5000);
  } catch (sameOriginError) { api.report("media020.sameOrigin.error", String(sameOriginError)); }
  api.report("media020.direct.complete", "same-origin-v6-requested");
  api.setStatus("DIRECT MEDIA TEST");
  api.setDetail("Explicit MP4 SVG video; check TV and request logs");
}
