// theme.js
(function(){
  const htmlEl   = document.documentElement;
  const btn      = document.getElementById("lightBtn");
  const logoImg  = document.getElementById("brandLogo");

  const logoDark = (window.STATIC_URL || "") + (logoImg?.getAttribute("data-dark") || "lightoff_logo.png");
  const logoLight= (window.STATIC_URL || "") + (logoImg?.getAttribute("data-light")|| "lighton_logo.png");

  function updateLogo(isLight){
    if (!logoImg) return;
    logoImg.src = isLight ? logoLight : logoDark;
    logoImg.alt = isLight ? "Brand logo (lights on)" : "Brand logo (lights off)";
  }

  function updateThemeColorMeta(){
    let m = document.querySelector('meta[name="theme-color"]');
    if(!m){ m=document.createElement('meta'); m.name='theme-color'; document.head.appendChild(m); }
    const bg = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
    m.content = bg || (htmlEl.dataset.theme === 'light' ? '#ffffff' : '#0e1420');
  }

  function setTheme(isLight){
    htmlEl.setAttribute("data-theme", isLight ? "light" : "dark");
    if (btn){
      btn.textContent = `Lights: ${isLight ? "On" : "Off"}`;
      btn.setAttribute("aria-pressed", String(isLight));
    }
    updateLogo(isLight);
    updateThemeColorMeta();

    const heroVideo = document.getElementById("heroVid");
    if (heroVideo){
      const newSrc = isLight ? (window.STATIC_URL || "") + "file5.mp4"
                             : (window.STATIC_URL || "") + "file4.mp4";
      if (!heroVideo.src.endsWith(newSrc)){
        heroVideo.src = newSrc;
        heroVideo.load();
        heroVideo.play().catch(()=>{});
      }
    }

    if (window.waterStage && typeof window.waterStage.transitionTo === 'function'){
      window.waterStage.transitionTo(isLight);
    }
  }

  let isLight = false;
  updateLogo(isLight);
  updateThemeColorMeta();

  if (btn){
    btn.addEventListener("click", ()=>{
      isLight = !isLight;
      setTheme(isLight);
    });
  }
})();
