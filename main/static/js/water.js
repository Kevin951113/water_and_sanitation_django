// water.js
(function(){
  function ensureGsapReady(cb){
    if (window.gsap || window.__gsapReady__) return cb();
    const id = setInterval(()=>{
      if (window.gsap || window.__gsapReady__){
        clearInterval(id); cb();
      }
    }, 50);
  }

  function initWaterStage(){
    const canvas = document.getElementById('water-canvas');
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    const DPR = window.devicePixelRatio || 1;

    let vw=0, vh=0;
    const state = { baseLevel: 0, colorT: 0 };

    function resize(){
      vw = window.innerWidth; vh = window.innerHeight;
      canvas.width = vw * DPR; canvas.height = vh * DPR;
      canvas.style.width = vw+'px'; canvas.style.height = vh+'px';
      ctx.setTransform(DPR,0,0,DPR,0,0);
    }
    window.addEventListener('resize', resize);
    resize();

    function drawFlat(level){
      ctx.clearRect(0,0,vw,vh);
      ctx.fillStyle = '#0e6fc0';
      ctx.fillRect(0, level, vw, vh-level);
    }

    state.baseLevel = vh * 0.18;
    drawFlat(state.baseLevel);

    return {
      transitionTo(isLight){
        const target = isLight ? vh*0.80 : vh*0.18;
        const start = state.baseLevel;
        const dur = 900; // ms
        const t0 = performance.now();

        function tick(now){
          const t = Math.min(1, (now - t0)/dur);
          state.baseLevel = start + (target - start) * (1 - Math.cos(t*Math.PI))/2; // easeInOut
          drawFlat(state.baseLevel);
          if (t<1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      }
    };
  }

  ensureGsapReady(function(){
    window.waterStage = initWaterStage();
  });
})();
