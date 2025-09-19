import React, { useEffect, useMemo, useRef, useState } from "react";

// Sea Treasure Hunt — React single‑file game (with surface jump + underwater scene)
// Controls: ← → to move, E to enter an air pocket, R to restart, P to pause
// Dataset: Load a JSON file formatted as [{ question, options:[...], answerIndex }] OR
// a CSV where each row is: question, options_semi_colon_separated, answerIndex
// Example CSV row: "Capital of Australia?,Canberra;Sydney;Melbourne;Perth,0"

// ======== Small helpers ========
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const randInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const uid = () => Math.random().toString(36).slice(2, 10);

function parseCSVLoose(text) {
  // CSV format: question, option1;option2;option3;option4, answerIndex
  // Robust line splitting for both \n and \r\n
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const items = [];
  for (const line of lines) {
    // split only on first and last comma to tolerate commas in the question
    const firstComma = line.indexOf(",");
    const lastComma = line.lastIndexOf(",");
    if (firstComma === -1 || lastComma === -1 || lastComma === firstComma) continue;
    const q = line.slice(0, firstComma).trim();
    const optionsRaw = line.slice(firstComma + 1, lastComma).trim();
    const idxRaw = line.slice(lastComma + 1).trim();
    const options = optionsRaw.split(";").map((s) => s.trim()).filter(Boolean);
    const answerIndex = Number(idxRaw);
    if (!q || !options.length || Number.isNaN(answerIndex)) continue;
    items.push({ question: q, options, answerIndex });
  }
  return items;
}

// Some sample questions (used if user doesn't load a dataset yet)
const SAMPLE_QUESTIONS = [
  {
    question: "What gas do humans need to breathe?",
    options: ["Oxygen", "Nitrogen", "Carbon Dioxide", "Helium"],
    answerIndex: 0,
  },
  {
    question: "Which ocean is the largest?",
    options: ["Indian", "Pacific", "Atlantic", "Arctic"],
    answerIndex: 1,
  },
  {
    question: "2 + 2 = ?",
    options: ["3", "4", "5", "22"],
    answerIndex: 1,
  },
  {
    question: "The capital of Australia is…",
    options: ["Canberra", "Sydney", "Melbourne", "Perth"],
    answerIndex: 0,
  },
];

// ======== Main Game ========
export default function SeaTreasureHunt() {
  // Viewport & world
  const VIEW_W = 960; // logical width
  const VIEW_H = 600; // logical height
  const WORLD_H = 5200; // world depth (y from 0 to WORLD_H)

  // World layers reference
  const WATER_SURFACE_Y = 110; // y where sea begins (below is water)
  const GROUND_Y = WORLD_H - 80;

  // Game state
  const [gameState, setGameState] = useState("menu"); // menu | intro | playing | paused | question | gameover | win
  const [oxygen, setOxygen] = useState(100);
  const [score, setScore] = useState(0);
  const [soundOn, setSoundOn] = useState(true);
  const [mobileControls, setMobileControls] = useState(false);
  const [splash, setSplash] = useState(null); // {x,y,ttl}

  const player = useRef({ x: VIEW_W / 2, y: 20, vx: 0, vy: 0 }); // starts above water for intro jump
  const keys = useRef({ left: false, right: false });
  const lastTs = useRef(0);

  // Questions management
  const [questions, setQuestions] = useState(SAMPLE_QUESTIONS);
  const [activePocketId, setActivePocketId] = useState(null);
  const [answeredPocketIds, setAnsweredPocketIds] = useState(new Set());
  const [currentQ, setCurrentQ] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);

  // Generate pockets (checkpoints requiring a question)
  const pockets = useMemo(() => {
    const N = 8; // number of air pockets
    const arr = [];
    let y = 400; // first pocket depth
    for (let i = 0; i < N; i++) {
      arr.push({ id: uid(), x: randInt(120, VIEW_W - 120), y, radius: 38, qIndex: i });
      y += randInt(500, 720);
    }
    return arr;
  }, []);

  const treasure = useMemo(() => ({ x: randInt(160, VIEW_W - 160), y: WORLD_H - 140, w: 120, h: 80 }), []);

  // Camera: follow player Y, clamped to world
  const camY = clamp(player.current.y - VIEW_H * 0.35, 0, WORLD_H - VIEW_H);

  // Keyboard controls
  useEffect(() => {
    const onKey = (e) => {
      if (e.type === "keydown") {
        if (e.key === "ArrowLeft" || e.key.toLowerCase() === "a") keys.current.left = true;
        if (e.key === "ArrowRight" || e.key.toLowerCase() === "d") keys.current.right = true;
        if (e.key.toLowerCase() === "p") togglePause();
        if (e.key.toLowerCase() === "r") restart();
        if (e.key.toLowerCase() === "e") attemptEnterPocket();
      } else {
        if (e.key === "ArrowLeft" || e.key.toLowerCase() === "a") keys.current.left = false;
        if (e.key === "ArrowRight" || e.key.toLowerCase() === "d") keys.current.right = false;
      }
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("keyup", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("keyup", onKey);
    };
  }, []);

  // Game loop
  useEffect(() => {
    let raf;
    const step = (ts) => {
      raf = requestAnimationFrame(step);
      const dt = Math.min(33, ts - (lastTs.current || ts));
      lastTs.current = ts;

      const px = player.current;

      if (gameState === "intro") {
        // Above-surface jump into sea
        const gravity = 0.36;
        px.vy += gravity;
        px.y += px.vy;
        // Gentle left-right control while falling
        if (keys.current.left) px.vx = clamp(px.vx - 0.4, -3, 3);
        else if (keys.current.right) px.vx = clamp(px.vx + 0.4, -3, 3);
        else px.vx *= 0.9;
        px.x = clamp(px.x + px.vx, 30, VIEW_W - 30);

        // Hit the water surface
        if (px.y >= WATER_SURFACE_Y) {
          setSplash({ x: px.x, y: WATER_SURFACE_Y, ttl: 900 });
          px.vy = 0; // dampen immediately
          setGameState("playing");
        }
      }

      if (gameState === "playing") {
        // Water movement: neutral buoyancy + slow descent
        const accel = 0.6; // control accel
        const maxSpeed = 3.3;
        if (keys.current.left) px.vx = clamp(px.vx - accel, -maxSpeed, maxSpeed);
        else if (keys.current.right) px.vx = clamp(px.vx + accel, -maxSpeed, maxSpeed);
        else px.vx *= 0.90; // damp

        px.x = clamp(px.x + px.vx, 30, VIEW_W - 30);
        px.y = clamp(px.y + 0.9, 20, WORLD_H - 40); // slow descent

        // Oxygen drain
        setOxygen((o) => {
          const next = clamp(o - 0.018 * (dt / 16.67), 0, 100);
          if (next <= 0) setGameState("gameover");
          return next;
        });

        // Score counts depth safely traversed
        setScore((s) => Math.max(s, Math.floor(px.y)));
      }

      // Splash TTL
      if (splash) {
        setSplash((sp) => (sp ? { ...sp, ttl: sp.ttl - dt } : null));
      }
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [gameState, splash]);

  function start() {
    // Reset player slightly above surface and give a tiny upward arc (optional)
    player.current = { x: VIEW_W / 2, y: 20, vx: 0.6, vy: -1.2 };
    setOxygen(100);
    setScore(0);
    setAnsweredPocketIds(new Set());
    setActivePocketId(null);
    setCurrentQ(null);
    setSelectedOption(null);
    setSplash(null);
    setGameState("intro");
  }
  function togglePause() {
    setGameState((st) => (st === "playing" ? "paused" : st === "paused" ? "playing" : st));
  }
  function restart() {
    player.current = { x: VIEW_W / 2, y: 20, vx: 0, vy: 0 };
    setOxygen(100);
    setScore(0);
    setAnsweredPocketIds(new Set());
    setActivePocketId(null);
    setCurrentQ(null);
    setSelectedOption(null);
    setSplash(null);
    setGameState("intro");
  }

  function nearestEnterablePocketId() {
    const px = player.current;
    let best = null;
    let bestDist = Infinity;
    for (const p of pockets) {
      if (answeredPocketIds.has(p.id)) continue; // already cleared
      const dist = Math.hypot(px.x - p.x, px.y - p.y);
      if (dist < bestDist) {
        bestDist = dist;
        best = p;
      }
    }
    if (!best) return null;
    const enterThreshold = best.radius + 18 + 8; // 18 ~ player radius, +8 slack
    return bestDist <= enterThreshold ? best.id : null;
  }

  function attemptEnterPocket() {
    if (!(gameState === "playing" || gameState === "intro")) return;
    const id = nearestEnterablePocketId();
    if (!id) return;
    const p = pockets.find((x) => x.id === id);
    if (!p) return;
    setActivePocketId(id);
    setCurrentQ(questions[(p.qIndex ?? 0) % questions.length]);
    setSelectedOption(null);
    setGameState("question");
  }

  function submitAnswer() {
    if (!currentQ) return;
    if (selectedOption == null) return;
    const correct = Number(selectedOption) === Number(currentQ.answerIndex);
    if (correct) {
      const newSet = new Set(answeredPocketIds);
      if (activePocketId) newSet.add(activePocketId);
      setAnsweredPocketIds(newSet);
      setOxygen((o) => clamp(o + 40, 0, 100));
      setActivePocketId(null);
      setCurrentQ(null);
      setSelectedOption(null);
      setGameState("playing");
    } else {
      setGameState("gameover");
    }
  }

  // Win condition
  useEffect(() => {
    if (gameState !== "playing") return;
    const px = player.current;
    const insideTreasure =
      px.x > treasure.x - 40 && px.x < treasure.x + treasure.w + 40 &&
      px.y > treasure.y - 10 && px.y < treasure.y + treasure.h + 10;
    if (insideTreasure) setGameState("win");
  }, [gameState, treasure]);

  // Dataset loaders
  function handleJSONUpload(text) {
    try {
      const obj = JSON.parse(text);
      if (!Array.isArray(obj)) throw new Error("JSON must be an array");
      const cleaned = obj
        .map((r) => ({ question: r.question, options: r.options, answerIndex: r.answerIndex }))
        .filter((r) => r && r.question && Array.isArray(r.options) && r.options.length >= 2 && Number.isFinite(r.answerIndex));
      if (!cleaned.length) throw new Error("No valid rows found");
      setQuestions(cleaned);
      alert(`Loaded ${cleaned.length} questions.`);
    } catch (e) {
      alert("JSON parse error: " + e.message);
    }
  }

  function handleCSVUpload(text) {
    const rows = parseCSVLoose(text);
    if (!rows.length) {
      alert("No valid CSV rows found.\nExpected: question, option1;option2;..., answerIndex");
      return;
    }
    setQuestions(rows);
    alert(`Loaded ${rows.length} questions.`);
  }

  function onFileChange(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "");
      if (f.name.toLowerCase().endsWith(".json")) handleJSONUpload(text);
      else handleCSVUpload(text);
    };
    reader.readAsText(f);
    e.target.value = ""; // reset
  }

  // Mobile buttons
  const touchLeft = () => {
    keys.current.left = true;
    setTimeout(() => (keys.current.left = false), 120);
  };
  const touchRight = () => {
    keys.current.right = true;
    setTimeout(() => (keys.current.right = false), 120);
  };

  // === Renders ===
  const uiOverlay = (
    <div className="absolute inset-x-0 top-0 p-3 flex items-center justify-between text-white select-none">
      <div className="flex items-center gap-3">
        <div className="w-56 h-5 rounded-full bg-white/20 shadow-inner overflow-hidden">
          <div className="h-full bg-emerald-300/90" style={{ width: `${oxygen}%` }} />
        </div>
        <span className="text-sm tracking-wide">O₂: {oxygen.toFixed(0)}%</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span>Depth: {Math.max(0, Math.floor(player.current.y - WATER_SURFACE_Y))} m</span>
        <span className="opacity-50">•</span>
        <span>Score: {score}</span>
      </div>
    </div>
  );

  const hudHints = (
    <div className="absolute bottom-3 inset-x-0 flex items-center justify-center text-white/80 text-sm pointer-events-none">
      <div className="px-3 py-1 bg-black/30 rounded-full backdrop-blur">
        Use ← → to swim; get <b>inside</b> the bubble and press <b>E</b>
      </div>
    </div>
  );

  const menuScreen = (
    <div className="absolute inset-0 grid place-items-center text-white">
      <div className="max-w-xl text-center p-6 rounded-3xl bg-black/30 backdrop-blur shadow-2xl">
        <h1 className="text-3xl md:text-4xl font-black tracking-tight">Sea Treasure Hunt</h1>
        <p className="mt-3 text-white/80">Jump from the surface and dive through the depths. Reach air pockets and answer questions to survive. Find the treasure at the ocean floor!</p>
        <div className="mt-6 flex items-center justify-center gap-3 flex-wrap">
          <Button onClick={start}>Start</Button>
          <label className="cursor-pointer">
            <input type="file" accept=".json,.csv" className="hidden" onChange={onFileChange} />
            <span className="px-4 py-2 rounded-2xl shadow-md border border-white/20 bg-white/10 hover:bg-white/20">Load Dataset (.json or .csv)</span>
          </label>
          <Button onClick={() => setMobileControls((v) => !v)} className={mobileControls ? "ring-2 ring-white" : ""}>
            {mobileControls ? "Hide" : "Show"} Mobile Controls
          </Button>
        </div>
        <details className="mt-4 text-left open:shadow-inner">
          <summary className="cursor-pointer text-white/90">Dataset format help</summary>
          <div className="mt-2 text-sm text-white/80 space-y-2">
            <p><b>JSON</b>: <code>[{`{ question, options:[..], answerIndex }`}]</code></p>
            <p><b>CSV</b>: <code>question, option1;option2;option3;option4, answerIndex</code></p>
            <p>Example JSON:</p>
            <pre className="bg-black/40 p-2 rounded">{JSON.stringify(SAMPLE_QUESTIONS, null, 2)}</pre>
            <p>Tip: Pockets use questions in order, looping if there are fewer questions than pockets.</p>
          </div>
        </details>
      </div>
    </div>
  );

  const pauseScreen = (
    <div className="absolute inset-0 grid place-items-center">
      <div className="px-6 py-4 rounded-2xl bg-black/40 text-white text-center">
        <h2 className="text-2xl font-bold mb-2">Paused</h2>
        <div className="flex gap-3 justify-center">
          <Button onClick={togglePause}>Resume</Button>
          <Button onClick={restart}>Restart</Button>
        </div>
      </div>
    </div>
  );

  const gameOverScreen = (
    <div className="absolute inset-0 grid place-items-center">
      <div className="px-6 py-4 rounded-2xl bg-black/60 text-white text-center">
        <h2 className="text-2xl font-bold">Out of Oxygen</h2>
        <p className="mt-1 text-white/80">You blacked out before reaching the treasure.</p>
        <div className="mt-3 flex gap-3 justify-center">
          <Button onClick={restart}>Try Again</Button>
          <Button onClick={() => setGameState("menu")}>Main Menu</Button>
        </div>
      </div>
    </div>
  );

  const winScreen = (
    <div className="absolute inset-0 grid place-items-center">
      <div className="px-6 py-4 rounded-2xl bg-black/60 text-white text-center">
        <h2 className="text-2xl font-bold">You found the Treasure! 🏴‍☠️</h2>
        <p className="mt-1 text-white/80">Depth reached: {Math.max(0, Math.floor(player.current.y - WATER_SURFACE_Y))} m</p>
        <div className="mt-3 flex gap-3 justify-center">
          <Button onClick={restart}>Play Again</Button>
          <Button onClick={() => setGameState("menu")}>Main Menu</Button>
        </div>
      </div>
    </div>
  );

  const questionModal = (
    <div className="absolute inset-0 grid place-items-center">
      <div className="max-w-xl w-[90%] px-6 py-5 rounded-3xl bg-black/70 backdrop-blur text-white shadow-2xl">
        <h3 className="text-xl font-bold">Air Pocket Challenge</h3>
        <p className="mt-2 text-white/90">{currentQ?.question}</p>
        <div className="mt-4 grid gap-2">
          {currentQ?.options?.map((opt, i) => (
            <Button key={i} className={`w-full text-left ${selectedOption === i ? "bg-white/25" : ""}`} onClick={() => setSelectedOption(i)}>
              <span className="opacity-70 mr-2">{String.fromCharCode(65 + i)}.</span> {opt}
            </Button>
          ))}
        </div>
        <div className="mt-4 flex gap-3 justify-end">
          <Button onClick={() => setGameState("playing")}>Cancel</Button>
          <Button onClick={submitAnswer} className="bg-emerald-400/90 text-black hover:bg-emerald-300">Submit</Button>
        </div>
      </div>
    </div>
  );

  // Background layers (sky + water)
  function renderSkyAndSurface() {
    return (
      <>
        {/* Sky */}
        <div className="absolute left-0 w-full" style={{ top: 0 - camY }}>
          <div className="h-[160px] w-full" style={{
            background: "linear-gradient(#8ec5ff 0%, #67a8ff 60%, #3e7be0 100%)",
          }} />
        </div>
        {/* Sun and clouds */}
        <div className="absolute left-10" style={{ top: 20 - camY }}>
          <div className="w-16 h-16 rounded-full bg-yellow-200/80 blur-sm" />
        </div>
        <div className="absolute right-20" style={{ top: 50 - camY }}>
          <div className="w-28 h-10 rounded-full bg-white/70 blur-[1px]" />
        </div>
        {/* Water surface (waves) */}
        <div className="absolute left-0 w-full" style={{ top: WATER_SURFACE_Y - camY }}>
          <div className="h-[6px] w-full bg-white/80 opacity-70" />
          <div className="h-3 w-full bg-blue-500/50" />
        </div>
      </>
    );
  }

  const gradientSea = (
    <div className="absolute inset-0" style={{
      background: "linear-gradient(#003a7a 0%, #00244d 50%, #00142b 100%)",
    }} />
  );

  function renderCaustics() {
    // light rays that move with cam
    return (
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="absolute rotate-12 bg-white/6"
            style={{
              left: (i * 150) % VIEW_W,
              top: -200 + ((i * 90 + camY * 0.3) % VIEW_H),
              width: 2,
              height: 300,
              filter: "blur(2px)",
            }}
          />
        ))}
      </div>
    );
  }

  function renderBubbles() {
    return (
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <div key={i} className="absolute rounded-full bg-white/25"
            style={{
              width: 4 + (i % 4) * 2,
              height: 4 + (i % 4) * 2,
              left: (i * 127) % VIEW_W,
              top: ((i * 173) % VIEW_H) + (camY * 0.2) % VIEW_H,
              filter: "blur(0.5px)",
            }}
          />
        ))}
      </div>
    );
  }

  function renderSeaweed() {
    return (
      <div className="absolute w-full" style={{ left: 0, top: GROUND_Y - camY }}>
        {[...Array(12)].map((_, i) => (
          <div key={i} className="absolute bottom-0" style={{ left: 20 + i * 80 }}>
            <div className="w-2 h-12 bg-emerald-600/70 rounded-t-full" />
            <div className="w-2 h-6 bg-emerald-700/70 rounded-t-full ml-2" />
          </div>
        ))}
      </div>
    );
  }

  function renderPocket(p) {
    const cleared = answeredPocketIds.has(p.id);
    const nearId = nearestEnterablePocketId();
    const near = (gameState === "playing" || gameState === "intro") && nearId === p.id;
    return (
      <div key={p.id} className="absolute" style={{ left: p.x - p.radius, top: p.y - camY - p.radius }}>
        <div
          className={`rounded-full border-2 ${cleared ? "border-emerald-300" : "border-cyan-200"} bg-white/5 relative`}
          style={{ width: p.radius * 2, height: p.radius * 2 }}
        >
          {near && (
            <div className="absolute inset-0 rounded-full animate-pulse" style={{ boxShadow: "0 0 24px rgba(56, 189, 248, 0.7)" }} />
          )}
        </div>
        {near && (
          <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[12px] px-2 py-0.5 rounded-full bg-black/60 text-white/90">
            Press <b>E</b> to enter
          </div>
        )}
      </div>
    );
  }

  function renderTreasure() {
    return (
      <div className="absolute" style={{ left: treasure.x, top: treasure.y - camY }}>
        <div className="w-[120px] h-[80px] rounded-xl bg-amber-500/80 border-4 border-amber-300 shadow-[0_0_30px_rgba(255,200,0,0.4)] grid place-items-center">
          <span className="text-black font-extrabold">TREASURE</span>
        </div>
      </div>
    );
  }

  function renderSeabed() {
    return (
      <div className="absolute w-full" style={{ left: 0, top: GROUND_Y - camY }}>
        <div className="h-16 w-full bg-yellow-900/60 border-t-4 border-yellow-700" />
      </div>
    );
  }

  function renderDiver() {
    const px = player.current;
    const aboveWater = px.y < WATER_SURFACE_Y;
    const body = (
      <div className="w-8 h-8 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/30 border border-white/40 relative">
        {/* snorkel */}
        <div className="absolute -right-3 top-1 w-3 h-2 bg-cyan-200/80 rounded-r" />
        {/* mask/bubble */}
        <div className="absolute left-1 top-5 w-2 h-2 bg-cyan-100/90 rounded-full" />
      </div>
    );
    const splashRing = splash && splash.ttl > 0 && (
      <div className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white/70 opacity-75"
           style={{ left: splash.x, top: splash.y - camY, width: 40, height: 14 }} />
    );

    return (
      <>
        <div className="absolute" style={{ left: px.x - 16, top: px.y - camY - 16 }}>
          <div className={`${aboveWater ? "animate-pulse" : ""}`}>{body}</div>
        </div>
        {splashRing}
      </>
    );
  }

  return (
    <div className="min-h-screen w-full bg-slate-900 text-white flex items-center justify-center p-2">
      <div className="relative" style={{ width: VIEW_W, height: VIEW_H }}>
        {/* World container */}
        <div className="absolute inset-0 overflow-hidden rounded-3xl border border-white/10 shadow-2xl">
          {gradientSea}
          {renderSkyAndSurface()}
          {renderCaustics()}
          {renderBubbles()}

          {/* World space */}
          <div className="absolute left-0 top-0" style={{ width: VIEW_W, height: VIEW_H }}>
            {renderSeabed()}
            {renderSeaweed()}
            {renderTreasure()}
            {pockets.map(renderPocket)}
            {renderDiver()}
          </div>

          {uiOverlay}
          {(gameState === "playing" || gameState === "intro") && hudHints}

          {gameState === "menu" && menuScreen}
          {gameState === "paused" && pauseScreen}
          {gameState === "gameover" && gameOverScreen}
          {gameState === "win" && winScreen}
          {gameState === "question" && questionModal}

          {/* Top‑right quick controls */}
          {gameState !== "menu" && (
            <div className="absolute top-3 right-3 flex gap-2">
              <Button onClick={() => setGameState((s) => (s === "paused" ? "playing" : s === "playing" ? "paused" : s))}>{gameState === "paused" ? "Resume" : "Pause"}</Button>
              <Button onClick={restart}>Restart</Button>
              <label className="cursor-pointer">
                <input type="file" accept=".json,.csv" className="hidden" onChange={onFileChange} />
                <span className="px-4 py-2 rounded-2xl shadow-md border border-white/20 bg-white/10 hover:bg-white/20">Load Qs</span>
              </label>
            </div>
          )}

          {/* Mobile controls */}
          {mobileControls && (gameState === "playing" || gameState === "intro") && (
            <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-6">
              <Button onClick={touchLeft} className="w-24">←</Button>
              <Button onClick={attemptEnterPocket} className="w-24">E</Button>
              <Button onClick={touchRight} className="w-24">→</Button>
            </div>
          )}
        </div>

        {/* Footer legend */}
        <div className="absolute -bottom-10 left-0 right-0 text-center text-white/60 text-sm select-none">
          Start: jump from surface • ← → move • E enter pocket • R restart • P pause
        </div>
      </div>
    </div>
  );
}

function Button({ children, className = "", ...props }) {
  return (
    <button
      className={`px-4 py-2 rounded-2xl shadow-md active:scale-[0.98] transition border border-white/20 bg-white/10 hover:bg-white/20 text-white ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

// =====================
// DEV TESTS (add ?devtest to URL to run)
// =====================
(function runDevTests() {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  if (!params.has("devtest")) return;

  const assert = (cond, msg) => {
    if (!cond) throw new Error("Test failed: " + msg);
    console.log("✔", msg);
  };

  // Test 1: Basic CSV parsing (Unix newlines)
  const csv1 = [
    "Q1?,A;B;C;D,2",
    "Q2?,Yes;No,0",
  ].join("\n");
  const rows1 = parseCSVLoose(csv1);
  assert(rows1.length === 2, "rows1 length 2");
  assert(rows1[0].question === "Q1?", "rows1[0] question");
  assert(rows1[0].options.length === 4, "rows1[0] 4 options");
  assert(rows1[0].answerIndex === 2, "rows1[0] answerIndex 2");

  // Test 2: Windows newlines and commas in question
  const csv2 = "What, if any, is X?,Opt1;Opt2,1\r\nAnother?,Y;N,0";
  const rows2 = parseCSVLoose(csv2);
  assert(rows2.length === 2, "rows2 length 2");
  assert(rows2[0].question.startsWith("What, if any"), "rows2[0] preserves comma in question");

  // Test 3: Trimming and empty options ignored
  const csv3 = "Question?, ;Opt; ;Opt2,1";
  const rows3 = parseCSVLoose(csv3);
  assert(rows3[0].options.includes("Opt") && rows3[0].options.includes("Opt2"), "rows3 trims empty options");

  // Test 4: Invalid rows skipped
  const csv4 = "BadRowWithNoCommas\nValid?,A;B,1";
  const rows4 = parseCSVLoose(csv4);
  assert(rows4.length === 1 && rows4[0].question === "Valid?", "invalid rows skipped");

  // Test 5: Trailing newline ignored
  const csv5 = "Alpha?,Yes;No,0\n";
  const rows5 = parseCSVLoose(csv5);
  assert(rows5.length === 1 && rows5[0].question === "Alpha?", "trailing newline ignored");

  // Test 6: Spaces around separators are trimmed
  const csv6 = "Trim?,  A ; B  ;  C ,1";
  const rows6 = parseCSVLoose(csv6);
  assert(rows6[0].options[0] === "A" && rows6[0].options[2] === "C", "options trimmed correctly");

  console.log("All dev tests passed.\n(Disable by removing ?devtest from the URL.)");
})();
