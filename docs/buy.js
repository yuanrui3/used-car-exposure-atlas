"use strict";
const $ = (id) => document.getElementById(id);
const money = (n) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
const percent = (n) => (n > 0 ? "+" : "") + Number(n).toFixed(1) + "%";
const byFips = new Map(GEO.counties.map((row) => [row[0], row]));
const countyName = (row) => row[1] + ", " + row[2];
const byName = new Map(
  GEO.counties.map((row) => [countyName(row).toLowerCase(), row[0]]),
);
const getFips = (input) =>
  byFips.has(input.trim())
    ? input.trim()
    : byName.get(input.trim().toLowerCase());
const counties = new Map();
const histories = [[], []];
const get = (i, key) => $(key + i);
const number = (i, key) => Number(get(i, key).value);
const hazardNames = [
  "Winter and road salt",
  "Coastal salt air",
  "Moisture",
  "Heat and sun",
  "Cold",
  "Grade",
  "Traffic",
  "Pavement",
  "Dust",
  "Flood events",
  "Hail events",
];
function field(i, key, label, value, type = "number", extra = "") {
  const props = type === "number" ? 'min="0" step="any"' : 'maxlength="180"';
  return (
    "<label>" +
    label +
    '<input id="' +
    key +
    i +
    '" type="' +
    type +
    '" ' +
    props +
    ' value="' +
    value +
    '" ' +
    extra +
    "></label>"
  );
}
function car(i) {
  const local = i === 0;
  return (
    '<article class="car"><h2>' +
    (local ? "Local car" : "Away car") +
    '</h2><div class="fieldgrid">' +
    field(
      i,
      "location",
      "Seller location",
      local ? "West Lafayette, IN" : "Schererville, IN",
      "text",
    ) +
    field(i, "minutes", "Drive one way (min)", local ? 0 : 90) +
    '<label class="wide">Price source<select id="mode' +
    i +
    '"><option value="estimate">Estimate from asking price</option><option value="quote">Written out-the-door quote</option></select></label></div>' +
    '<div class="fieldgrid" id="estimate' +
    i +
    '">' +
    field(i, "ask", "Asking price ($)", local ? 26420 : 25420) +
    field(i, "tax", "Vehicle sales/use tax (%)", 7, "number", 'max="100"') +
    field(i, "taxfees", "Additional taxable fees ($)", 0) +
    field(i, "other", "Title, registration & other non-taxable fees ($)", 0) +
    "</div>" +
    '<div class="fieldgrid" id="quote' +
    i +
    '" hidden>' +
    field(
      i,
      "otd",
      "Written out-the-door total ($)",
      "",
      "number",
      'placeholder="Enter dealer quote"',
    ) +
    field(i, "unpaid", "Home tax or fees still owed ($)", 0) +
    "</div>" +
    '<p class="note" id="modenote' +
    i +
    '"></p><div class="fieldgrid">' +
    field(i, "travel", "Total trip costs ($)", local ? 0 : 45) +
    field(i, "hours", "Total travel time (hours)", local ? 0 : 3) +
    field(i, "inspection", "Inspection cost ($)", 0) +
    field(i, "financing", "Total financing charges ($)", 0) +
    "</div>" +
    '<a class="route" id="directions' +
    i +
    '" target="_blank" rel="noopener">Check driving directions ↗</a>' +
    '<p class="cashout" id="subtotal' +
    i +
    '">—</p>' +
    '<details><summary>Vehicle history and repair estimates</summary><div><p class="note">Look up counties where this car was registered or regularly driven. Exposure points to items to inspect. Enter a mechanic’s repair range for the same ownership horizon on both cars.</p>' +
    '<label>Past county<input id="history' +
    i +
    '" list="countyList" placeholder="County, state" autocomplete="off"></label>' +
    '<button type="button" class="addHistory" data-i="' +
    i +
    '">Add past county</button><p class="note" id="histmsg' +
    i +
    '"></p><ul class="histrows" id="histlist' +
    i +
    '"></ul>' +
    '<div class="fieldgrid">' +
    field(
      i,
      "low",
      "Repair estimate, low ($)",
      "",
      "number",
      'placeholder="Unknown"',
    ) +
    field(
      i,
      "high",
      "Repair estimate, high ($)",
      "",
      "number",
      'placeholder="Unknown"',
    ) +
    "</div></div></details></article>"
  );
}
$("cars").innerHTML = car(0) + car(1);
function summary(i, timeValue) {
  const mode = get(i, "mode").value;
  get(i, "estimate").hidden = mode === "quote";
  get(i, "quote").hidden = mode !== "quote";
  get(i, "modenote").textContent =
    mode === "quote"
      ? "Include the full purchase before down payment or trade-in. Add only charges outstanding after the quote."
      : "Simple cash estimate without a trade-in or exemption. Enter only fees beyond the asking price. For an interstate purchase, use the written quote and any remaining home-state charges.";
  const needed =
    mode === "quote" ? ["otd", "unpaid"] : ["ask", "tax", "taxfees", "other"];
  const valid = [
    ...needed,
    "travel",
    "hours",
    "inspection",
    "financing",
    "minutes",
  ].every((k) => get(i, k).value !== "" && get(i, k).checkValidity());
  const taxable = number(i, "ask") + number(i, "taxfees");
  const purchase =
    mode === "quote"
      ? number(i, "otd") + number(i, "unpaid")
      : taxable * (1 + number(i, "tax") / 100) + number(i, "other");
  const total =
    purchase +
    number(i, "travel") +
    timeValue * number(i, "hours") +
    number(i, "inspection") +
    number(i, "financing");
  const lo = get(i, "low").value,
    hi = get(i, "high").value;
  const rangeValid =
    lo !== "" &&
    hi !== "" &&
    get(i, "low").checkValidity() &&
    get(i, "high").checkValidity() &&
    Number(lo) <= Number(hi);
  const rangeIncomplete = (lo !== "" || hi !== "") && !rangeValid;
  get(i, "subtotal").textContent = valid
    ? "Before repairs · " + money(total)
    : "Complete the price and trip fields";
  const src = $("origin").value.trim(),
    end = get(i, "location").value.trim();
  const link = get(i, "directions");
  link.hidden = !src || !end;
  if (src && end)
    link.href =
      "https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=" +
      encodeURIComponent(src) +
      "&destination=" +
      encodeURIComponent(end);
  return {
    valid,
    total,
    rangeValid,
    rangeIncomplete,
    low: Number(lo),
    high: Number(hi),
  };
}
function update() {
  const time = Number($("timevalue").value),
    a = summary(0, time),
    b = summary(1, time);
  const valid =
    a.valid &&
    b.valid &&
    ["timevalue", "radius"].every(
      (k) => $(k).value !== "" && $(k).checkValidity(),
    );
  const delta = a.total - b.total,
    over = number(1, "minutes") > Number($("radius").value);
  $("resultLabel").textContent = "Difference before repairs";
  $("resultValue").textContent = valid ? money(Math.abs(delta)) : "—";
  $("resultLead").textContent = !valid
    ? ""
    : delta > 0
      ? "lower for the away car"
      : delta < 0
        ? "lower for the local car"
        : "same modeled cost";
  let title = "Enter both quotes and trip costs",
    detail =
      "Use comparable year, trim, drivetrain, miles, title, warranty and condition.";
  if (valid) {
    title = over
      ? "Away seller exceeds your drive limit"
      : "What would change the decision?";
    if (a.rangeIncomplete || b.rangeIncomplete) {
      detail =
        "Each repair range needs two nonnegative amounts, with the low estimate first.";
    } else if (a.rangeValid && b.rangeValid) {
      const low = delta + a.low - b.high,
        high = delta + a.high - b.low;
      if (low > 0) {
        title = over ? title : "Away car costs less across the repair range";
        detail =
          "Away savings including repairs: " +
          money(low) +
          " to " +
          money(high) +
          ".";
      } else if (high < 0) {
        title = over ? title : "Local car costs less across the repair range";
        detail =
          "Local savings including repairs: " +
          money(-high) +
          " to " +
          money(-low) +
          ".";
      } else {
        title = over ? title : "The repair ranges overlap";
        detail =
          "Depending on repair costs, the result ranges from " +
          money(-low) +
          " in favor of local to " +
          money(high) +
          " in favor of away.";
      }
    } else {
      detail =
        delta === 0
          ? "Any additional fee or repair breaks the tie."
          : (delta > 0 ? "The away car" : "The local car") +
            " can need " +
            money(Math.abs(delta)) +
            " more in repairs than the other car before its savings disappear. Get VIN history and a written inspection estimate.";
    }
  }
  $("decisionTitle").textContent = title;
  $("decisionDetail").textContent = detail;
}
function paintHistory(i) {
  const list = get(i, "histlist");
  list.replaceChildren();
  for (const f of histories[i]) {
    const v = counties.get(f),
      li = document.createElement("li");
    const top = v.hazards
      .map((score, j) => ({ score, j }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
    li.textContent =
      countyName(byFips.get(f)) +
      " · annual exposure " +
      v.exposure.toFixed(1) +
      "/100. Highest national category percentiles: " +
      top.map((k) => hazardNames[k.j] + " " + Math.round(k.score)).join(", ") +
      ". ";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "Remove";
    btn.onclick = () => {
      histories[i] = histories[i].filter((c) => c !== f);
      paintHistory(i);
    };
    li.append(btn);
    list.append(li);
  }
}
for (const btn of document.querySelectorAll(".addHistory"))
  btn.onclick = () => {
    const i = +btn.dataset.i,
      f = getFips(get(i, "history").value);
    if (!f || !counties.has(f)) {
      get(i, "histmsg").textContent =
        "Select a listed county or enter a five-digit county FIPS.";
      return;
    }
    if (!histories[i].includes(f)) histories[i].push(f);
    get(i, "history").value = "";
    get(i, "histmsg").textContent = "";
    paintHistory(i);
  };
document.querySelector(".buy").addEventListener("input", (evt) => {
  if (evt.target.matches("input,select") && evt.target.id !== "marketChoice")
    update();
});
const ns = "http://www.w3.org/2000/svg";
function el(name, attrs) {
  const n = document.createElementNS(ns, name);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}
let selected = "18157";
function showCounty(f) {
  if (!byFips.has(f) || !counties.has(f)) return;
  selected = f;
  const row = byFips.get(f),
    v = counties.get(f);
  $("marketChoice").value = countyName(row);
  $("mapselection").setAttribute("d", row[5]);
  const info = $("marketInfo");
  info.replaceChildren();
  function write(tag, txt) {
    const e = document.createElement(tag);
    e.textContent = txt;
    info.append(e);
  }
  write("h3", countyName(row));
  if (v.pct === null) {
    write("strong", "No estimate");
    write(
      "p",
      v.n +
        " supported listing" +
        (v.n === 1 ? "" : "s") +
        " across " +
        v.families +
        " model families. Coverage is too thin or concentrated.",
    );
  } else {
    write("strong", percent(v.pct));
    write(
      "p",
      "Median adjusted asking-price difference vs. the national benchmark.",
    );
    write(
      "p",
      v.n +
        " listings · " +
        v.families +
        " model families. Conditional bootstrap range " +
        percent(v.lo) +
        " to " +
        percent(v.hi) +
        ".",
    );
  }
  write(
    "p",
    "Annual vehicle exposure: " +
      v.exposure.toFixed(1) +
      "/100 for a car that spent time here.",
  );
}
function color(v) {
  return v === null
    ? "#e0e4e4"
    : v < -10
      ? "#19706d"
      : v < -4
        ? "#6eaaa0"
        : v < 4
          ? "#f3ecce"
          : v < 10
            ? "#dba077"
            : "#b95b3b";
}
function renderMap() {
  const svg = $("map"),
    frag = document.createDocumentFragment();
  for (const row of GEO.counties) {
    const v = counties.get(row[0]);
    const path = el("path", {
      d: row[5],
      fill: color(v?.pct ?? null),
      class: "mapcounty",
      "data-fips": row[0],
    });
    const title = el("title", {});
    title.textContent =
      countyName(row) +
      " · " +
      (v?.pct != null ? percent(v.pct) : "Insufficient data");
    path.append(title);
    frag.append(path);
  }
  for (const state of GEO.states)
    frag.append(
      el("path", {
        d: state[2],
        fill: "none",
        stroke: "#7c9392",
        "stroke-width": ".7",
        "pointer-events": "none",
      }),
    );
  frag.append(el("path", { id: "mapselection" }));
  svg.append(frag);
  svg.addEventListener("click", (e) => {
    const f = e.target.dataset.fips;
    if (f) showCounty(f);
  });
  const options = document.createDocumentFragment();
  for (const row of [...GEO.counties].sort((a, b) =>
    countyName(a).localeCompare(countyName(b)),
  )) {
    const o = document.createElement("option");
    o.value = countyName(row);
    options.append(o);
  }
  $("countyList").append(options);
  showCounty(selected);
  $("marketChoice").oninput = (e) => {
    const f = getFips(e.target.value);
    if (f) showCounty(f);
    else
      $("marketInfo").textContent =
        "Choose a county from the list or enter a five-digit county FIPS.";
  };
  $("useDest").onclick = () => {
    const f = getFips($("marketChoice").value);
    if (!f) return;
    clearQuote(1);
    get(1, "location").value = countyName(byFips.get(f));
    $("exampleNote").textContent =
      "Enter a written away quote and the drive time to the actual seller.";
    update();
    $("quotes").scrollIntoView();
  };
}
update();
fetch("assets/county-shopping.json")
  .then((r) => {
    if (!r.ok) throw Error();
    return r.json();
  })
  .then((data) => {
    for (const [f, v] of Object.entries(data.counties))
      counties.set(f, {
        n: v[0],
        families: v[1],
        pct: v[2],
        lo: v[3],
        hi: v[4],
        exposure: v[5],
        hazards: v.slice(6),
      });
    const m = data.summary;
    renderMap();
    $("methods").innerHTML =
      "<p>September 29–November 2, 2026. Of " +
      m.raw.toLocaleString() +
      " Craigslist ads, " +
      m.eligible.toLocaleString() +
      " listings remained after vehicle, clean-title, location and duplicate checks. Condition is seller-reported. Exact model descriptions, seller type, year, drivetrain, fuel, transmission, condition and a 5,000-mile window yielded only " +
      m.strict_matched +
      " listings with three outside comparables across two counties. No county met the exact-match publication threshold.</p><p>The displayed estimates use a log-price regression controlling for make, model text, model family and year, mileage, condition, seller type, fuel, body, transmission and drive. Each prediction came from a model trained outside the listing’s county. " +
      m.shown +
      " of 3,108 counties met coverage rules. A county needs at least 40 supported listings across eight model families with no family above 25%. The median absolute price prediction error on individual supported listings was " +
      m.median_abs_pct_error +
      '%. Family-bootstrap intervals omit model specification, seller selection and negotiation uncertainty.</p><p>Compare actual written quotes before travelling. The fit uses advertised amounts before taxes and buyer-specific fees. Undisclosed prior damage, omitted trim details and uneven representation of sellers can change the result. <a href="https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data/versions/11">Listing source</a> · <a href="assets/county-shopping.csv" download>Download county results</a> · <a href="https://github.com/yuanrui3/used-car-exposure-atlas/tree/main/research/shopping">Methods and analysis code</a></p>';
  })
  .catch(() => {
    $("marketInfo").textContent =
      "County data could not load. Refresh to try again. The quote calculator is available above.";
  });
const routes = [
  {
    from: "Eagan, MN",
    to: "Cambridge, MN",
    counties: "Dakota → Isanti",
    minutes: 67,
    discount: 16.4,
    levels: "61.8 → 42.7",
    sample: "242 / 273",
    check: "Six near-pairs showed a median 11.7% lower ask.",
    source: "https://www.trippy.com/drive/Eagan-to-Cambridge-MN",
  },
  {
    from: "Minneapolis, MN",
    to: "Cambridge, MN",
    counties: "Hennepin → Isanti",
    minutes: 55,
    discount: 11.0,
    levels: "61.4 → 42.7",
    sample: "208 / 273",
    check: "Four near-pairs showed a median 8.0% lower ask.",
    source:
      "https://www.travelmath.com/driving-time/from/Minneapolis,+MN/to/Cambridge,+MN",
  },
  {
    from: "Anoka, MN",
    to: "Cambridge, MN",
    counties: "Anoka → Isanti",
    minutes: 42,
    discount: 18.7,
    levels: "53.1 → 42.7",
    sample: "256 / 273",
    check: "Six near-pairs showed a smaller 4.4% median discount.",
    source: "https://www.trippy.com/distance/Anoka-to-Cambridge-MN",
  },
  {
    from: "Hillsboro, OR",
    to: "Vancouver, WA",
    counties: "Washington (OR) → Clark (WA)",
    minutes: 36,
    discount: 8.0,
    levels: "54.5 → 47.9",
    sample: "197 / 245",
    check: "Five near-pairs showed a median 9.3% lower ask.",
    source:
      "https://www.travelmath.com/driving-time/from/Hillsboro,+OR/to/Vancouver,+WA",
  },
];
function clearQuote(i) {
  get(i, "mode").value = "quote";
  for (const k of [
    "otd",
    "ask",
    "low",
    "high",
    "tax",
    "travel",
    "hours",
    "minutes",
  ])
    get(i, k).value = "";
  for (const k of ["unpaid", "other", "taxfees", "inspection", "financing"])
    get(i, k).value = 0;
  histories[i] = [];
  paintHistory(i);
  get(i, "history").value = "";
}
for (const r of routes) {
  const card = document.createElement("article");
  card.className = "routecard";
  card.innerHTML =
    "<h3>" +
    r.from +
    " → " +
    r.to +
    '</h3><p class="note">' +
    r.counties +
    " · " +
    r.minutes +
    " min one way</p><p><b>" +
    r.discount.toFixed(1) +
    "% lower adjusted asking price</b><br>Annual exposure " +
    r.levels +
    " on the 0–100 scale. Supported listings, origin / destination: " +
    r.sample +
    '.</p><p class="note">' +
    r.check +
    '</p><button type="button">Compare quotes on this route</button><a href="' +
    r.source +
    '">Drive time ↗</a>';
  card.querySelector("button").onclick = () => {
    for (let i = 0; i < 2; i++) clearQuote(i);
    $("origin").value = r.from;
    get(0, "location").value = r.from;
    get(1, "location").value = r.to;
    get(0, "minutes").value = 0;
    get(0, "hours").value = 0;
    get(0, "travel").value = 0;
    get(1, "minutes").value = r.minutes;
    get(1, "hours").value = ((2 * r.minutes) / 60).toFixed(2);
    if (r.from.endsWith("MN"))
      for (let i = 0; i < 2; i++) get(i, "tax").value = 6.875;
    $("exampleNote").textContent =
      "Enter both written quotes for your registration address and the away trip’s costs. The round-trip time assumes one visit. Verify prior registration counties before comparing exposure.";
    update();
    $("quotes").scrollIntoView();
    get(0, "otd").focus({ preventScroll: true });
  };
  $("routeCards").append(card);
}
