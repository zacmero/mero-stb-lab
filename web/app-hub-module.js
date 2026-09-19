function meroHubModule(api) {
  var marker = "MERO-USB-CAP-012-7B3D9E21";
  var candidates = [
    "file:///proc/version",
    "file:///etc/os-release",
    "file:///etc/hostname",
    "file:///media/MERO_STB/MERO_USB_012.txt",
    "file:///mnt/MERO_STB/MERO_USB_012.txt",
    "file:///mnt/usb/MERO_USB_012.txt",
    "file:///media/usb/MERO_USB_012.txt",
    "file:///tmp/mnt/MERO_STB/MERO_USB_012.txt",
    "usb:///MERO_USB_012.txt"
  ];
  var cycle = 0;

  function clean(value) {
    return String(value).replace(/[\r\n\t]+/g, " ").substr(0, 240);
  }

  function label(uri) {
    var value = uri.replace(/^file:\/\//, "file-").replace(/[^A-Za-z0-9]+/g, ".");
    return value.replace(/^\.+|\.+$/g, "").substr(0, 100);
  }

  function reportResult(prefix, uri, status, content) {
    var text = clean(content || "");
    api.report(prefix + "." + label(uri), "status=" + status + ";bytes=" + text.length + ";body=" + text);
    if (text.indexOf(marker) >= 0) {
      api.report("usb.marker.found", prefix + ":" + uri);
      api.setStatus("USB MARKER FOUND");
      api.setDetail(uri);
    }
  }

  function xhrAt(index, done) {
    var request, uri, active = true, deadline;
    if (index >= candidates.length) {
      done();
      return;
    }
    uri = candidates[index];
    function finish(status, content) {
      if (!active) {
        return;
      }
      active = false;
      clearTimeout(deadline);
      reportResult("xhr", uri, status, content);
      xhrAt(index + 1, done);
    }
    try {
      request = new XMLHttpRequest();
      request.onreadystatechange = function () {
        if (request.readyState == 4) {
          finish(request.status, request.responseText);
        }
      };
      request.open("GET", uri, true);
      request.send(null);
      deadline = setTimeout(function () { finish("timeout", ""); }, 2500);
    } catch (error) {
      finish("throw", clean(error));
    }
  }

  function nativeAt(index, done) {
    var uri, active = true, deadline;
    if (index >= candidates.length) {
      done();
      return;
    }
    uri = candidates[index];
    function finish(status, content) {
      if (!active) {
        return;
      }
      active = false;
      clearTimeout(deadline);
      reportResult("geturl", uri, status, content);
      nativeAt(index + 1, done);
    }
    try {
      getURL(uri, function (result) {
        try {
          finish(result.success, result.content);
        } catch (error) {
          finish("callback-error", clean(error));
        }
      });
      deadline = setTimeout(function () { finish("timeout", ""); }, 2500);
    } catch (error2) {
      finish("throw", clean(error2));
    }
  }

  function runCycle() {
    cycle++;
    api.setStatus("USB / LOCAL FILE PROBE");
    api.setDetail("Read-only cycle " + cycle + " of 12");
    api.report("usb.cycle", cycle);
    xhrAt(0, function () {
      nativeAt(0, function () {
        api.report("usb.cycle.complete", cycle);
        if (cycle < 12) {
          setTimeout(runCycle, 15000);
        } else {
          api.setStatus("USB PROBE COMPLETE");
          api.setDetail("Keyboard events remain active; cleanup from workstation");
          api.report("usb.probe.complete", "yes");
        }
      });
    });
  }

  function key(event) {
    api.report("usb.key.last", "code=" + (event.keyCode || event.which || 0) + ";type=" + event.type);
  }

  api.report("usb.probe.version", "USB-CAP-012-v1");
  api.report("usb.getURL.type", typeof getURL);
  api.report("usb.marker.expected", marker);
  document.documentElement.addEventListener("keydown", key, false);
  document.documentElement.addEventListener("keypress", key, false);
  document.documentElement.addEventListener("keyup", key, false);
  setTimeout(runCycle, 300);
}
