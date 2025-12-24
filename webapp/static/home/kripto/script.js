/* --------------  ASRIN GLOBAL 3-D MENU  -------------- */

document.addEventListener("DOMContentLoaded", () => {
  if (!window.location.pathname.startsWith("/kripto")) return;
  (() => {
    /* ----------  Sabitler  ---------- */
    const MIN_ITEMS = 25; // her listede min. öğe
    const staticBase = window.STATIC_BASE || "/static/data/";

    /* ----------  DOM  ---------- */
    const $ = (s) => document.querySelector(s);
    const list3d = $("#menu3d");
    const choiceBox = $("#choices");
    const choiceOL = $("#choices ol");
    const selectBtn = $("#selectBtn");
    const backBtn = $("#backBtn");

    /* ----------  Durum  ---------- */
    let items = []; // ekranda dönen liste
    let idx = 0; // aktif indeks
    const path = []; // [{id,ad,altHizmetler?}, …]

    /* ----------  Yardımcı  ---------- */
    const fetchJSON = (file) => fetch(staticBase + file).then((r) => r.json());

    /* ----------  Başlat: HUB listesi  ---------- */
    fetchJSON("hubs.json").then(showList);

    /* ----------  Listeyi çiz + otomatik spacer  ---------- */
    function showList(arr) {
      items = [...arr];
      while (items.length < MIN_ITEMS)
        items.push({ id: `autoSpacer${items.length}`, ad: "—", spacer: true });

      list3d.innerHTML = "";
      const rot = -360 / items.length;
      list3d.style.setProperty("--rotateDegrees", rot);

      items.forEach((it, i) => {
        const li = document.createElement("li");
        li.style.setProperty("--day_idx", i);
        li.innerHTML = `<span>${it.ad}</span>`;
        if (it.spacer || it.id.startsWith("spacer")) li.classList.add("spacer");
        li.onclick = () => choose(i);
        list3d.append(li);
      });
      idx = 0;
      highlight();
      toggleUI();
    }

    /* ----------  Aktif öğeyi vurgula  ---------- */
    function highlight() {
      if (!items.length) return;
      list3d.style.setProperty("--currentDay", idx);
      list3d
        .querySelectorAll("li")
        .forEach((li) => li.classList.remove("active"));
      const act = list3d.children[idx];
      if (act) {
        act.classList.add("active");
        document.body.style.background = getComputedStyle(act).backgroundColor;
      }
    }

    /* ----------  Yukarı / Aşağı  ---------- */
    function adjust(step) {
      if (!items.length) return;
      idx = (idx + step + items.length) % items.length;
      highlight();
    }
    window.adjust = adjust;
    window.addEventListener("keydown", (e) => {
      if (e.key === "ArrowUp") adjust(-1);
      if (e.key === "ArrowDown") adjust(1);
    });

    /* ----------  Seç & Geri butonları  ---------- */
    selectBtn.onclick = () => choose(idx);
    backBtn.onclick = goBack;

    /* ----------  Seçim mantığı  ---------- */
    function choose(i) {
      const sel = items[i];
      if (sel.spacer || sel.id.startsWith("spacer")) return; // boş öğe

      // panel görünür & zincire ekle
      const li = document.createElement("li");
      li.textContent = sel.ad;
      choiceOL.append(li);
      path.push(sel);
      toggleUI();

      if (path.length === 1) {
        fetchJSON(`services.${sel.id}.json`).then((d) =>
          showList(d.anaHizmetler)
        );
      } else if (sel.altHizmetler) {
        showList(sel.altHizmetler);
      } else {
        const hub = path[0].id,
          ana = path[1] ? path[1].id : "",
          url = `/hub/${hub}/${ana}/${sel.id}`;
        // window.location.href = url;        // rotanızı burada ayarlayın
        console.log(
          "Geliştirme modunda seçilen yol:",
          `${hub} › ${ana} › ${sel.id}`
        );
      }
    }

    /* ----------  Geri işlemi  ---------- */
    function goBack() {
      if (!path.length) return;
      path.pop(); // son seçimi at
      choiceOL.lastChild.remove();
      toggleUI();

      if (!path.length) {
        fetchJSON("hubs.json").then(showList); // köke dön
      } else if (path.length === 1) {
        fetchJSON(`services.${path[0].id}.json`).then((d) =>
          showList(d.anaHizmetler)
        );
      } else {
        showList(path[path.length - 1].altHizmetler);
      }
    }

    /* ----------  Panel & Geri butonu görünüm  ---------- */
    function toggleUI() {
      if (path.length === 0) {
        choiceBox.classList.add("hidden");
        backBtn.classList.add("hidden");
      } else {
        choiceBox.classList.remove("hidden");
        backBtn.classList.remove("hidden");
      }
    }
  })();
});
