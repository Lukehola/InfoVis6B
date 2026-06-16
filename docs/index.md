---
layout: default
title: NBA vs WNBA
---

<iframe
  id="notebook-frame"
  src="notebook.html"
  title="NBA vs WNBA notebook"
  loading="eager"
  style="width: 100%; min-height: 100vh; border: 0; display: block; background: white;"
></iframe>

<script>
  (function () {
    var f = document.getElementById('notebook-frame');

    function measureHeight(doc) {
      var b = doc.body, h = doc.documentElement;
      return Math.max(
        b ? b.scrollHeight  : 0,
        b ? b.offsetHeight  : 0,
        h ? h.clientHeight  : 0,
        h ? h.scrollHeight  : 0,
        h ? h.offsetHeight  : 0
      );
    }

    function resize() {
      try {
        var doc = f.contentDocument || f.contentWindow.document;
        if (!doc) return;
        var h = measureHeight(doc);
        if (h && h > 200) f.style.height = (h + 80) + 'px';
      } catch (e) { /* same-origin so shouldn't fire */ }
    }

    function attachObserver() {
      try {
        var doc = f.contentDocument || f.contentWindow.document;
        if (!doc || !doc.body) return;
        resize();
        if (typeof ResizeObserver !== 'undefined') {
          new ResizeObserver(resize).observe(doc.body);
        }
        // also poll for ~30s in case async chart embeds keep growing the body
        var ticks = 0;
        var iv = setInterval(function () {
          resize();
          if (++ticks > 40) clearInterval(iv);
        }, 750);
      } catch (e) {}
    }

    f.addEventListener('load', attachObserver);
    window.addEventListener('resize', resize);
  })();
</script>

<style>
  /* Let the iframe span the full Cayman content area */
  .main-content { max-width: 96% !important; padding: 1.5rem 2% 2rem 2% !important; }
  @media (min-width: 1100px) { .main-content { max-width: 1080px !important; padding: 1.5rem 0 2rem 0 !important; margin: 0 auto !important; } }
</style>
