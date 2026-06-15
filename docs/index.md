---
layout: default
title: NBA vs WNBA — A Data Story
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
    function resize() {
      try {
        var h = f.contentDocument.body.scrollHeight;
        if (h && h > 200) f.style.height = (h + 60) + 'px';
      } catch (e) { /* cross-origin guard, shouldn't fire on same origin */ }
    }
    f.addEventListener('load', resize);
    window.addEventListener('resize', resize);
    // re-check periodically — chart rendering can grow the body after onload
    setInterval(resize, 800);
  })();
</script>

<style>
  /* Let the iframe span the full Cayman content area */
  .main-content { max-width: 96% !important; padding: 1.5rem 2% 2rem 2% !important; }
  @media (min-width: 1100px) { .main-content { max-width: 1080px !important; padding: 1.5rem 0 2rem 0 !important; margin: 0 auto !important; } }
</style>
