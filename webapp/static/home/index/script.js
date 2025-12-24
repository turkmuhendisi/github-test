/* =======================================================================================|
                TABLE OF CONTENTS – script.js                                             |
   =======================================================================================|
   | №  | Bölüm              | Satır (yaklaşık) | Ne yapar?                               |
   |----|--------------------|------------------|-----------------------------------------|
   | A  | Genel Ayarlar & Veri Yükleme | 1-34   | JSON’u fetch eder, globaller tanımlar   |
   | B  | Yardımcı Fonksiyonlar        | 36-86  | GSAP kısayolları, luma hesaplama vb.    |
   | C  | Durum Değişkenleri           | 88-99  | Otomatik süre, koordinatlar vs.         |
   | D  | DOM Oluşturma                |101-131 | Kart & içerik HTML’sini üretir          |
   | E  | Parlaklık Algısı             |133-165 | Küçük kart kontrastı & luma saklar      |
   | F  | Video Oynatma                |167-185 | Aktif kart videolarını oynat/durdur     |
   | G  | init() – İlk Yerleşim        |187-265 | Tüm elemanları ilk kez konumlandırır    |
   | H  | step() – Kaydırma            |267-361 | İleri/geri animasyon & panel kontrastı  |
   | I  | loop() – Otomatik Tur        |363-372 | Progress bar + sonsuz döngü             |
   | J  | Görsel Preload               |374-387 | Resimleri yükler, videoları atlar       |
   | K  | Olay Bağlama                 |389-408 | Ok düğmeleri + pencere resize           |
   | L  | Başlatıcı                    |410-426 | fetch → preload → init → run            |
   =======================================================================================|
*/

/* ============================================================
   A ░ GENEL AYARLAR & VERİ YÜKLEME
   ========================================================== */

/* ① Global veri dizisi – JSON’dan sonra dolacak */
let data = [];

/* ② slides.json dosyasını fetch eder */
async function loadData() {
  const res = await fetch("/slides/");
  if (!res.ok) throw new Error("slides.json not found");
  const json = await res.json();
  data = json; // globali güncelle
  return json; // istersek geri de döndür
}
/* ============================================================
   B ░ YARDIMCI FONKSİYONLAR
   ========================================================== */

const _ = (id) => document.getElementById(id);
const set = gsap.set;
const ease = "sine.inOut";
const numberSize = 50;

const getCard = (i) => `#card${i}`;
const getCardContent = (i) => `#card-content-${i}`;
const getSliderItem = (i) => `#slide-item-${i}`;
const isVideo = (src) => src.toLowerCase().endsWith(".mp4");

/* GSAP Promise wrapper */
function animate(target, duration, props) {
  return new Promise((r) =>
    gsap.to(target, { ...props, duration, onComplete: r })
  );
}

/* ► Ortalama parlaklık (0–255) */
function getAverageLuma(img) {
  const c = document.createElement("canvas");
  c.width = c.height = 10; // 10×10 thumbnail
  const ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, 10, 10);
  const { data } = ctx.getImageData(0, 0, 10, 10);
  let total = 0;
  for (let i = 0; i < data.length; i += 4) {
    total += 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
  }
  return total / 100;
}

/* ► Discover düğmesi → sidebar */
function bindSidebar() {
  const sidebar = document.getElementById("sidebar");
  const closeBtn = document.getElementById("sidebar-close");

  sidebar.classList.remove("open");

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button.discover");
    if (!btn) return;

    e.stopPropagation();
    updateSidebarContent(order[0]);
    sidebar.classList.add("open");
    console.log("Sidebar açıldı, details gizleniyor...");

    // ✅ Detayları gizle
    const details = document.querySelectorAll(".details");
    details.forEach((el) => {
      el.classList.add("details-hidden");
    });
  });

  closeBtn.addEventListener("click", () => {
    sidebar.classList.remove("open");

    // ✅ Detayları geri getir
    const details = document.querySelectorAll(".details");
    details.forEach((el) => {
      el.classList.remove("details-hidden");
    });
  });
}

/* ░░ Sidebar içeriğini doldurur ░░ */
function updateSidebarContent(idx) {
  const item = data[idx]; // ✅ önce item tanımlanır

  const sidebar = document.getElementById("sidebar");
  sidebar.classList.remove("light", "dark");
  sidebar.classList.add((item.luma ?? 255) < 128 ? "dark" : "light");

  const el = document.getElementById("sidebar-content");
  if (!el) return;

  const isVideo = (src) => src.toLowerCase().endsWith(".mp4");

  const raw = item.details || item.description;
  const parts = raw
    .split("•")
    .map((s) => s.trim())
    .filter(Boolean);

  const media = isVideo(item.image)
    ? `<video src="${item.image}" autoplay muted loop playsinline
         style="width: 100%; max-height: 180px; border-radius: 8px; object-fit: cover; margin-bottom: 12px;">
       </video>`
    : `<img src="${item.image}" alt="${item.title}"
         style="width: 100%; max-height: 180px; border-radius: 8px; object-fit: cover; margin-bottom: 12px;" />`;

  const html = `
    <div id="sidebar-structure">
      <!-- Üst Menü -->
      <div class="sidebar-top">
        <h3>${item.title} ${item.title2}</h3>
      </div>

      <!-- Orta İçerik -->
      <div class="sidebar-middle">
        ${media}
        <p>${parts.shift() || ""}</p>
        ${
          parts.length
            ? `<ul class="sb-list">${parts
                .map((t) => `<li>${t}</li>`)
                .join("")}</ul>`
            : ""
        }
      </div>

      <!-- Alt Bar -->
        <div class="sidebar-bottom">
          <input
            type="search"
            class="sidebar-search"
            placeholder="Bu içerikte ara..."
            onkeydown="if(event.key === 'Enter') openSearchModal(this.value)"
          />
        </div>
      </div>
  `;
  el.innerHTML = html;
}

/* ============================================================
   C ░ DURUM DEĞİŞKENLERİ
   ========================================================== */

const AUTO_DELAY = 10; // progress bar süresi (sn)
let order = []; // data geldikten sonra dolacak
let detailsEven = true;
let animating = false;

let offsetTop = 200,
  offsetLeft = 700,
  cardWidth = 200,
  cardHeight = 300,
  gap = 40;

/* ============================================================
   D ░ DOM OLUŞTURMA
   ========================================================== */

function buildDOM() {
  const cards = data
    .map((item, idx) =>
      isVideo(item.image)
        ? `<div class="card" id="card${idx}">
             <video src="${item.image}" preload="none" muted loop playsinline
                    style="width:100%;height:100%;object-fit:cover"></video>
           </div>`
        : `<div class="card" id="card${idx}"
             style="background-image:url(${item.image})"></div>`
    )
    .join("");

  const cardContents = data
    .map(
      (i, idx) => `
      <div class="card-content" id="card-content-${idx}">
        <div class="content-start"></div>
        <div class="content-place">${i.place}</div>
        <div class="content-title-1">${i.title}</div>
        <div class="content-title-2">${i.title2}</div>
      </div>`
    )
    .join("");

  _("demo").innerHTML = cards + cardContents;

  _("slide-numbers").innerHTML = data
    .map(
      (_, idx) => `<div class="item" id="slide-item-${idx}">${idx + 1}</div>`
    )
    .join("");
}

/* ============================================================
   E ░ PARLAKLIK ALGISI (küçük kart)
   ========================================================== */

function tagBrightness() {
  data.forEach((item, idx) => {
    /* video → doğrudan beyaz yazı */
    if (isVideo(item.image)) {
      document.getElementById(`card-content-${idx}`)?.classList.add("dark");
      item.luma = 0;
      return;
    }

    /* görsel → luma hesapla */
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      let luma = 255;
      try {
        luma = getAverageLuma(img);
      } catch (e) {}
      item.luma = luma;
      document
        .getElementById(`card-content-${idx}`)
        ?.classList.add(luma < 128 ? "dark" : "light");
    };
    img.src = item.image;
  });
}

/* ░░ Menü kontrastını güncelle ░░ */
function updateMenuContrast() {
  const nav = document.querySelector("nav");
  const luma = data[order[0]].luma ?? 255; // aktif kart parlaklığı
  if (luma < 128) {
    // koyu kart → beyaz yazı
    nav.classList.add("menu-light");
    nav.classList.remove("menu-dark");
  } else {
    // açık kart → siyah yazı
    nav.classList.add("menu-dark");
    nav.classList.remove("menu-light");
  }
}

/* ============================================================
   F ░ VİDEO OYNATMA KONTROLÜ
   ========================================================== */

function updateVideoPlayback(activeIdx) {
  data.forEach((item, idx) => {
    if (!isVideo(item.image)) return;
    const vid = document.querySelector(`#card${idx} video`);
    if (!vid) return;
    if (idx === activeIdx) {
      vid.play().catch(() => {});
    } else {
      vid.pause();
      vid.currentTime = 0;
    }
  });
}

/* ============================================================
   G ░ INIT – İLK YERLEŞİM
   ========================================================== */

function init() {
  const [active, ...rest] = order;
  const detailsActive = detailsEven ? "#details-even" : "#details-odd";
  const detailsInactive = detailsEven ? "#details-odd" : "#details-even";
  const { innerHeight: h, innerWidth: w } = window;

  /* konum hesapları */
  offsetTop = h - 430;
  offsetLeft = w - 830;

  /* nav, pagination, cover başlangıç */
  set("#pagination", {
    top: offsetTop + 330,
    left: offsetLeft,
    y: 200,
    opacity: 0,
    zIndex: 60,
  });
  set("nav", { y: -200, opacity: 0 });
  set(".indicator", { x: -w });

  /* aktif kart ekranı kaplasın */
  set(getCard(active), { x: 0, y: 0, width: w, height: h });
  set(getCardContent(active), { x: 0, y: 0, opacity: 0 });

  /* detay paneller başlangıç */
  [detailsActive, detailsInactive].forEach((sel, i) => {
    const base = i
      ? { opacity: 0, zIndex: 12 }
      : { opacity: 0, zIndex: 22, x: -200 };
    set(sel, base);
    [".text", ".title-1", ".title-2"].forEach((c) =>
      set(`${sel} ${c}`, { y: 100 })
    );
    set(`${sel} .desc`, { y: 50 });
    set(`${sel} .cta`, { y: 60 });
  });

  /* progress çubuğu */
  set(".progress-sub-foreground", {
    width: 500 * (1 / order.length) * (active + 1),
  });

  /* terastaki diğer kartlar */
  rest.forEach((i, idx) => {
    set(getCard(i), {
      x: offsetLeft + 400 + idx * (cardWidth + gap),
      y: offsetTop,
      width: cardWidth,
      height: cardHeight,
      zIndex: 30,
      borderRadius: 10,
    });
    set(getCardContent(i), {
      x: offsetLeft + 400 + idx * (cardWidth + gap),
      y: offsetTop + cardHeight - 100,
      zIndex: 40,
    });
    set(getSliderItem(i), { x: (idx + 1) * numberSize });
  });

  /* cover kalksın, diğer animasyonlar girsin */
  gsap.to(".cover", {
    x: w + 400,
    delay: 0.5,
    ease,
    onComplete: () => setTimeout(loop, 500),
  });
  rest.forEach((i, idx) => {
    gsap.to(getCard(i), {
      x: offsetLeft + idx * (cardWidth + gap),
      zIndex: 30,
      ease,
      delay: 0.6 + 0.05 * idx,
    });
    gsap.to(getCardContent(i), {
      x: offsetLeft + idx * (cardWidth + gap),
      zIndex: 40,
      ease,
      delay: 0.6 + 0.05 * idx,
    });
  });
  gsap.to("#pagination", { y: 0, opacity: 1, ease, delay: 0.6 });
  gsap.to("nav", { y: 0, opacity: 1, ease, delay: 0.6 });
  gsap.to(detailsActive, { opacity: 1, x: 0, ease, delay: 0.6 });

  /* video + panel kontrast */
  updateVideoPlayback(active);
  const initPanel = document.querySelector(detailsActive);
  initPanel.classList.remove("light", "dark");
  if (isVideo(data[active].image)) {
    initPanel.classList.add("dark");
  } else {
    initPanel.classList.add(
      (data[active].luma ?? 255) < 128 ? "dark" : "light"
    );
  }
  updateMenuContrast(); // <— ekleyin
}

/* ============================================================
   H ░ STEP – İLERİ / GERİ ANİMASYON
   ========================================================== */

function step(dir = 1) {
  if (animating) return;
  animating = true;

  /* sıra güncelle */
  dir === 1 ? order.push(order.shift()) : order.unshift(order.pop());
  detailsEven = !detailsEven;

  const detailsActive = detailsEven ? "#details-even" : "#details-odd";
  const detailsInactive = detailsEven ? "#details-odd" : "#details-even";
  const [active, ...rest] = order;
  const prv = rest[rest.length - 1];
  const activeData = data[active];

  /* metin güncelle */
  document.querySelector(`${detailsActive} .place-box .text`).textContent =
    activeData.place;
  document.querySelector(`${detailsActive} .title-1`).textContent =
    activeData.title;
  document.querySelector(`${detailsActive} .title-2`).textContent =
    activeData.title2;
  document.querySelector(`${detailsActive} .desc`).textContent =
    activeData.description;

  set(detailsActive, { zIndex: 22 });
  gsap.to(detailsActive, { opacity: 1, delay: 0.4, ease });
  [".text", ".title-1", ".title-2", ".desc", ".cta"].forEach((cls, k) =>
    gsap.to(`${detailsActive} ${cls}`, {
      y: 0,
      delay: 0.1 + 0.05 * k,
      duration: k < 3 ? 0.7 : 0.4,
      ease,
    })
  );
  set(detailsInactive, { zIndex: 12 });

  /* kart kaydırma */
  set(getCard(prv), { zIndex: 10 });
  set(getCard(active), { zIndex: 20 });
  gsap.to(getCard(prv), { scale: 1.5, ease });

  gsap.to(getCardContent(active), {
    y: offsetTop + cardHeight - 10,
    opacity: 0,
    duration: 0.3,
    ease,
  });
  gsap.to(getSliderItem(active), { x: 0, ease });
  gsap.to(getSliderItem(prv), { x: -dir * numberSize, ease });
  gsap.to(".progress-sub-foreground", {
    width: 500 * (1 / order.length) * (active + 1),
    ease,
  });

  /* ekranı kaplayan yeni kart */
  gsap.to(getCard(active), {
    x: 0,
    y: 0,
    width: window.innerWidth,
    height: window.innerHeight,
    borderRadius: 0,
    ease,
    onComplete: () => {
      /* ➊ Sidebar senkronizasyon */
      if (document.getElementById("sidebar").classList.contains("open")) {
        updateSidebarContent(active);
      }

      const xNew = offsetLeft + (rest.length - 1) * (cardWidth + gap);
      set(getCard(prv), {
        x: xNew,
        y: offsetTop,
        width: cardWidth,
        height: cardHeight,
        zIndex: 30,
        borderRadius: 10,
        scale: 1,
      });
      set(getCardContent(prv), {
        x: xNew,
        y: offsetTop + cardHeight - 100,
        opacity: 1,
        zIndex: 40,
      });
      set(getSliderItem(prv), { x: rest.length * numberSize });

      set(detailsInactive, { opacity: 0 });
      [".text", ".title-1", ".title-2"].forEach((c) =>
        set(`${detailsInactive} ${c}`, { y: 100 })
      );
      set(`${detailsInactive} .desc`, { y: 50 });
      set(`${detailsInactive} .cta`, { y: 60 });

      /* panel kontrast + video */
      const panel = document.querySelector(detailsActive);
      panel.classList.remove("light", "dark");
      if (isVideo(activeData.image)) {
        panel.classList.add("dark");
      } else {
        panel.classList.add((activeData.luma ?? 255) < 128 ? "dark" : "light");
      }
      updateVideoPlayback(active);
      animating = false;
      updateMenuContrast(); // <— kart değişince güncelle
    },
  });

  /* terastaki diğer kartlar */
  rest.forEach((i, idx) => {
    if (i === prv) return;
    const xNew = offsetLeft + idx * (cardWidth + gap);
    set(getCard(i), { zIndex: 30 });
    gsap.to(getCard(i), {
      x: xNew,
      y: offsetTop,
      width: cardWidth,
      height: cardHeight,
      ease,
      delay: 0.1 * (idx + 1),
    });
    gsap.to(getCardContent(i), {
      x: xNew,
      y: offsetTop + cardHeight - 100,
      opacity: 1,
      zIndex: 40,
      ease,
      delay: 0.1 * (idx + 1),
    });
    gsap.to(getSliderItem(i), { x: (idx + 1) * numberSize, ease });
  });
}

/* ============================================================
   I ░ LOOP – OTOMATİK TUR
   ========================================================== */

async function loop() {
  await animate(".indicator", AUTO_DELAY, { x: 0 });
  await animate(".indicator", AUTO_DELAY / 2, {
    x: window.innerWidth,
    delay: 0.3,
  });
  set(".indicator", { x: -window.innerWidth });
  step(1);
  loop();
}

/* ============================================================
   J ░ GÖRSEL PRELOAD
   ========================================================== */

function loadImages() {
  return Promise.all(
    data.map(({ image }) => {
      if (isVideo(image)) return Promise.resolve();
      return new Promise((res, rej) => {
        const img = new Image();
        img.onload = res;
        img.onerror = rej;
        img.src = image;
      });
    })
  );
}

/* ============================================================
   K ░ OLAY BAĞLAMA
   ========================================================== */

function bindArrows() {
  document.addEventListener("click", (e) => {
    const arrow = e.target.closest(".arrow");
    if (!arrow || animating) return;

    e.stopImmediatePropagation(); // ← kritik satır
    arrow.classList.contains("arrow-right") ? step(1) : step(-1);
  });
}

/* ► Hamburger menü */
function bindMenuToggle() {
  const btn = document.querySelector(".menu-toggle");
  const menu = document.querySelector(".menu-links");
  if (!btn || !menu) return;

  /* 1️⃣  Butona tıklarsak aç / kapa */
  btn.addEventListener("click", (e) => {
    e.stopPropagation(); // tıklama olayı belgede yukarı çıkmasın
    btn.classList.toggle("open");
    menu.classList.toggle("open");
  });

  /* 2️⃣  Sayfanın başka yerine tıklarsak kapa */
  document.addEventListener("click", (e) => {
    const clickOutside = !menu.contains(e.target) && !btn.contains(e.target);
    if (clickOutside && menu.classList.contains("open")) {
      btn.classList.remove("open");
      menu.classList.remove("open");
    }
  });

  // Menu Tıklayınca kapansın
  // menu.addEventListener("click", (e) => {
  //   if (e.target.tagName === "LI") {
  //     btn.classList.remove("open");
  //     menu.classList.remove("open");
  //   }
  // });
}

/* pencere yeniden boyutlanınca yeniden yerleşim */
function debounce(fn, ms = 250) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, a), ms);
  };
}
window.addEventListener("resize", debounce(init));

/* ============================================================
   N ░ LEFT-STRIP KAYDIRMA
   ============================================================ */
function stripTimeline() {
  const strip = document.querySelector("#strip-svg");
  if (!strip) return;

  const w = 1200; // viewBox genişliği
  gsap.fromTo(
    "#strip-icons",
    { x: 0 },
    {
      x: -w / 2, // yarım turda ikonlar sıfırlanacak
      duration: 20,
      ease: "linear",
      repeat: -1,
    }
  );
}

/* ============================================================
   L ░ BAŞLAT
   ========================================================== */
document.addEventListener("DOMContentLoaded", () => {
  if (window.location.pathname !== "/") return;
  const sidebar = document.getElementById("sidebar");
  sidebar?.classList.remove("open"); // ✨ sayfa ilk açıldığında sidebar kapalı başlasın
});

(async function start() {
  try {
    await loadData();
    order = data.map((_, i) => i);
    buildDOM();
    tagBrightness();
    await loadImages();
  } catch (err) {
    console.error("Başlatma hatası:", err);
  } finally {
    init();
    bindArrows();
    bindSidebar();
    bindMenuToggle();
  }
})();
