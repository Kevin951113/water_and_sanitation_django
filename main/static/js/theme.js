// theme.js
(function(){
  const htmlEl   = document.documentElement;
  const btn      = document.getElementById("lightBtn");
  const logoImg  = document.getElementById("brandLogo");

  // 取靜態路徑（Django 會把這些檔案放在同一個 static 目錄）
  const logoDark = (window.STATIC_URL || "") + (logoImg?.getAttribute("data-dark") || "lightoff_logo.png");
  const logoLight= (window.STATIC_URL || "") + (logoImg?.getAttribute("data-light")|| "lighton_logo.png");

  function updateLogo(isLight){
    if (!logoImg) return;
    // 若 img 原本就用 {% static %} 指向一張圖，也沒關係，JS 會覆蓋 src
    logoImg.src = isLight ? logoLight : logoDark;
    logoImg.alt = isLight ? "Brand logo (lights on)" : "Brand logo (lights off)";
  }

  function updateThemeColorMeta(){
    let m = document.querySelector('meta[name="theme-color"]');
    if(!m){ m=document.createElement('meta'); m.name='theme-color'; document.head.appendChild(m); }
    // 以 CSS 變數 --bg 當 theme-color，避免跳色
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

    // 切首頁 hero 影片（如果存在）
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

    // 通知水面動畫
    if (window.waterStage && typeof window.waterStage.transitionTo === 'function'){
      window.waterStage.transitionTo(isLight);
    }
  }

  // 初始狀態（預設 dark）
  let isLight = false;
  updateLogo(isLight);
  updateThemeColorMeta();

  // 綁定按鈕
  if (btn){
    btn.addEventListener("click", ()=>{
      isLight = !isLight;
      setTheme(isLight);
    });
  }
})();
