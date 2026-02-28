const map = L.map("map", { zoomControl: true }).setView([20.2308, 0.0], 2);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 7,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const categoryColor = (cat) => {
  const c = (cat || "").toLowerCase();
  if (c.includes("earthquake")) return "#d7263d";
  if (c.includes("wildfires") || c.includes("fire")) return "#ef6f00";
  if (c.includes("storms") || c.includes("cyclones")) return "#145f8a";
  if (c.includes("volcanoes")) return "#7d4f50";
  if (c.includes("humanitarian")) return "#5b8c5a";
  return "#34495e";
};

function toDateText(v) {
  if (!v) return "n/a";
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? v : d.toLocaleString("ja-JP", { timeZone: "UTC" }) + " UTC";
}

function safeHttpUrl(raw) {
  try {
    const u = new URL(String(raw || ""));
    if (u.protocol === "http:" || u.protocol === "https:") return u.toString();
    return null;
  } catch {
    return null;
  }
}

async function load() {
  const data = await fetch("./data/world.json", { cache: "no-store" }).then((r) => r.json());
  const briefText = await fetch("./data/daily_brief.md", { cache: "no-store" }).then((r) => r.text());

  document.getElementById("updatedAt").textContent = `updated: ${toDateText(data.generated_at)}`;
  document.getElementById("brief").textContent = briefText;

  const counts = {};
  for (const e of data.events) {
    counts[e.category] = (counts[e.category] || 0) + 1;
  }
  const countList = document.getElementById("counts");
  Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([cat, n]) => {
      const li = document.createElement("li");
      li.textContent = `${cat}: ${n}`;
      countList.appendChild(li);
    });

  const eventsRoot = document.getElementById("events");
  data.events
    .slice()
    .sort((a, b) => String(b.time || "").localeCompare(String(a.time || "")))
    .slice(0, 120)
    .forEach((e) => {
      if (typeof e.lat === "number" && typeof e.lon === "number") {
        L.circleMarker([e.lat, e.lon], {
          radius: 4,
          color: categoryColor(e.category),
          fillColor: categoryColor(e.category),
          fillOpacity: 0.7,
          weight: 1,
        })
          .addTo(map)
          .bindPopup(`<b>${escapeHtml(e.title)}</b><br>${escapeHtml(e.source)}<br>${escapeHtml(toDateText(e.time))}`);
      }

      const el = document.createElement("div");
      el.className = "event";

      const titleDiv = document.createElement("div");
      const titleStrong = document.createElement("strong");
      titleStrong.textContent = e.title || "Untitled";
      titleDiv.appendChild(titleStrong);
      el.appendChild(titleDiv);

      const metaDiv = document.createElement("div");
      metaDiv.className = "meta";
      metaDiv.textContent = `${e.source || "unknown"} | ${e.category || "other"} | ${toDateText(e.time)}`;

      const safeUrl = safeHttpUrl(e.url);
      if (safeUrl) {
        metaDiv.append(" ");
        const a = document.createElement("a");
        a.href = safeUrl;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = "source";
        metaDiv.appendChild(a);
      }

      el.appendChild(metaDiv);
      eventsRoot.appendChild(el);
    });
}

load().catch((err) => {
  document.getElementById("updatedAt").textContent = `load error: ${err}`;
});
