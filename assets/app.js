(function () {
  "use strict";

  var EMBED = window.__EMBEDDED_DATA__ || null;

  var state = {
    data: null,
    tab: "all",
    keyword: "",
    timer: null
  };

  var el = {
    list: document.getElementById("noticeList"),
    empty: document.getElementById("emptyTip"),
    tabs: document.getElementById("tabs"),
    search: document.getElementById("searchInput"),
    refresh: document.getElementById("refreshBtn"),
    lastSync: document.getElementById("lastSync"),
    nextSync: document.getElementById("nextSync"),
    countdown: document.getElementById("countdown"),
    total: document.getElementById("totalCount"),
    newCount: document.getElementById("newCount"),
    platform: document.getElementById("platformState"),
    platformLink: document.getElementById("platformLink"),
    official: document.getElementById("officialLinks"),
    sources: document.getElementById("sourceList"),
    syncHour: document.getElementById("syncHour"),
    footTime: document.getElementById("footTime"),
    mask: document.getElementById("drawerMask"),
    drawer: document.getElementById("drawer"),
    drawerTitle: document.getElementById("drawerTitle"),
    drawerMeta: document.getElementById("drawerMeta"),
    drawerBody: document.getElementById("drawerBody"),
    drawerOpen: document.getElementById("drawerOpen"),
    drawerClose: document.getElementById("drawerClose")
  };

  var CATEGORY_TAG = {
    "通知公告": "zxtz",
    "公示公告": "gsgg",
    "赛事动态": "race",
    "高校竞赛通知": "cxcy"
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function pad(n) { return n < 10 ? "0" + n : "" + n; }

  function fmtTime(iso) {
    if (!iso) return "—";
    return iso.replace("T", " ");
  }

  function matches(item, tab, kw) {
    if (tab === "cxcy" && !item.cxcy) return false;
    if (tab === "tournament" && !item.tournament) return false;
    if (tab === "zxtz" && item.sourceKey !== "zxtz") return false;
    if (tab === "gsgg" && item.sourceKey !== "gsgg") return false;
    if (tab === "lnut" && item.sourceKey !== "lnut") return false;
    if (!kw) return true;
    var hay = (item.title || "") + " " + (item.source || "") + " " + (item.tags || []).join(" ");
    return hay.toLowerCase().indexOf(kw.toLowerCase()) !== -1;
  }

  function renderList() {
    if (!state.data) return;
    var items = state.data.items || [];
    var kw = state.keyword.trim();
    var shown = items.filter(function (it) { return matches(it, state.tab, kw); });

    el.empty.hidden = shown.length > 0;
    if (!shown.length) {
      el.list.innerHTML = "";
      return;
    }

    el.list.innerHTML = shown.map(function (it) {
      var badges = [];
      var catCls = CATEGORY_TAG[it.category] || "";
      badges.push('<span class="badge ' + catCls + '">' + esc(it.category) + "</span>");
      if (it.cxcy && it.category !== "高校竞赛通知") badges.push('<span class="badge cxcy">创新创业</span>');
      if (it.isNew) badges.push('<span class="badge fresh">新</span>');

      var tags = (it.tags || []).filter(function (t) { return t.length > 1; }).slice(0, 2).map(function (t) {
        return '<span class="badge">' + esc(t) + "</span>";
      }).join("");

      return '<li class="notice" data-url="' + esc(it.url) + '" data-id="' + esc(it.id) + '" tabindex="0">' +
        '<div class="notice-top">' + badges.join("") + tags + "</div>" +
        "<h3>" + esc(it.title) + "</h3>" +
        '<div class="notice-meta">' +
          "<span>" + esc(it.date || "日期以官方页面为准") + "</span>" +
          "<span>" + esc(it.source) + "</span>" +
        "</div>" +
        '<span class="go">查看原文 →</span>' +
        "</li>";
    }).join("");
  }

  function renderCounts() {
    if (!state.data) return;
    var items = state.data.items || [];
    var c = state.data.counts || {};
    el.total.textContent = items.length;
    if (c.new) {
      el.newCount.textContent = "新增 " + c.new;
    } else {
      el.newCount.textContent = "";
    }
    var nums = { all: items.length, cxcy: c.cxcy || 0, tournament: c.tournament || 0 };
    Object.keys(nums).forEach(function (k) {
      var node = el.tabs.querySelector('[data-num="' + k + '"]');
      if (node) node.textContent = nums[k];
    });
  }

  function renderSide() {
    if (!state.data) return;
    el.official.innerHTML = (state.data.officialLinks || []).map(function (l) {
      return '<li><a href="' + esc(l.url) + '" target="_blank" rel="noopener noreferrer">' +
        "<strong>" + esc(l.name) + " ↗</strong>" +
        "<small>" + esc(l.desc || "") + "</small></a></li>";
    }).join("");

    el.sources.innerHTML = (state.data.sources || []).map(function (s) {
      var label = "正常 " + (s.count || 0) + " 条";
      var cls = "s-ok";
      if (s.status !== "ok") { label = "抓取失败"; cls = "s-bad"; }
      else if (s.stale) { label = "沿用缓存"; cls = "s-stale"; }
      return '<li><span class="s-name" title="' + esc(s.name) + '">' + esc(s.name) + "</span>" +
        '<span class="' + cls + '">' + label + "</span></li>";
    }).join("");

    var p = state.data.platform || {};
    if (p.ok) {
      el.platform.textContent = "可访问";
      el.platform.className = "state ok";
      el.platform.title = (p.title || "") + " · 检测于 " + (p.checkedAt || "");
    } else {
      el.platform.textContent = "暂不可达";
      el.platform.className = "state bad";
      el.platform.title = p.error || "";
    }

    if (state.data.syncHour != null) {
      el.syncHour.textContent = pad(state.data.syncHour) + ":00";
    }
  }

  function tickCountdown() {
    if (!state.data || !state.data.nextSync) {
      el.countdown.textContent = "";
      return;
    }
    var target = new Date(state.data.nextSync.replace(/-/g, "/")).getTime();
    var diff = target - Date.now();
    if (diff <= 0) {
      el.countdown.textContent = "即将同步…";
      return;
    }
    var h = Math.floor(diff / 3600000);
    var m = Math.floor((diff % 3600000) / 60000);
    var s = Math.floor((diff % 60000) / 1000);
    el.countdown.textContent = "还有 " + pad(h) + ":" + pad(m) + ":" + pad(s);
  }

  function openFromQuery() {
    var target = new URLSearchParams(location.search).get("view");
    if (!target || !state.data) return;
    var item = (state.data.items || []).filter(function (x) {
      return x.url === target || x.id === target;
    })[0];
    if (item) openDrawer(item);
  }

  function applyData(payload) {
    state.data = payload;
    el.lastSync.textContent = fmtTime(payload.generatedAt);
    el.nextSync.textContent = fmtTime(payload.nextSync);
    el.nextSync.title = "服务运行期间每天自动同步一次";
    renderCounts();
    renderList();
    renderSide();
    tickCountdown();
    openFromQuery();
  }

  function load() {
    if (EMBED) {
      document.body.setAttribute("data-mode", "static");
      applyData(EMBED);
      if (el.refresh) el.refresh.hidden = true;
      return;
    }
    el.list.innerHTML = '<li class="skeleton"></li><li class="skeleton"></li><li class="skeleton"></li>';
    return fetch("/api/data", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(applyData)
      .catch(function () {
        el.list.innerHTML = "";
        el.empty.hidden = false;
        el.empty.textContent = "读取本地数据失败，请确认服务已启动（python server.py）。";
      });
  }

  function doRefresh() {
    if (EMBED || !el.refresh) return;
    el.refresh.disabled = true;
    el.refresh.textContent = "同步中…";
    fetch("/api/refresh", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.ok) applyData(res.data);
      })
      .catch(function () {})
      .then(function () {
        el.refresh.disabled = false;
        el.refresh.textContent = "立即同步";
        clearTimeout(state.timer);
      });
  }

  /* ------------------------------------------------------------ drawer */
  function openDrawer(item) {
    var title = item.title;
    el.drawerTitle.textContent = title;
    el.drawerMeta.textContent = [item.date, item.source].filter(Boolean).join(" · ");
    el.drawerOpen.href = item.url;
    el.drawerBody.innerHTML = '<p class="loading-line">正在从官方页面读取原文…</p>';
    el.drawer.hidden = false;
    el.mask.hidden = false;
    document.body.style.overflow = "hidden";

    if (EMBED) {
      el.drawerBody.innerHTML = "<p>这份文件是离线快照，未内置正文。</p><p>点击下方「打开官方原文 ↗」可查看官方全文，标题、日期与链接均为官方原始内容。</p>";
      return;
    }

    fetch("/api/preview?url=" + encodeURIComponent(item.url), { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.ok && res.article && res.article.html) {
          el.drawerBody.innerHTML = res.article.html;
        } else {
          el.drawerBody.innerHTML = '<p>（预览暂不可用：' + esc((res && res.error) || "未知错误") +
            '）请点击下方「打开官方原文」查看。</p>';
        }
      })
      .catch(function () {
        el.drawerBody.innerHTML = '<p>（网络异常，无法读取原文）请点击下方「打开官方原文」查看。</p>';
      });
  }

  function closeDrawer() {
    el.drawer.hidden = true;
    el.mask.hidden = true;
    document.body.style.overflow = "";
    el.drawerBody.innerHTML = "";
  }

  /* ------------------------------------------------------------ events */
  el.list.addEventListener("click", function (e) {
    var li = e.target.closest(".notice");
    if (!li || !state.data) return;
    var item = (state.data.items || []).filter(function (x) { return x.id === li.dataset.id; })[0];
    if (item) openDrawer(item);
  });

  el.list.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var li = e.target.closest(".notice");
    if (!li) return;
    e.preventDefault();
    li.click();
  });

  el.tabs.addEventListener("click", function (e) {
    var btn = e.target.closest(".tab");
    if (!btn) return;
    Array.prototype.forEach.call(el.tabs.querySelectorAll(".tab"), function (b) {
      b.classList.toggle("active", b === btn);
    });
    state.tab = btn.dataset.tab;
    renderList();
  });

  var searchTimer = null;
  el.search.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      state.keyword = el.search.value;
      renderList();
    }, 160);
  });

  if (el.refresh) el.refresh.addEventListener("click", doRefresh);
  el.drawerClose.addEventListener("click", closeDrawer);
  el.mask.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !el.drawer.hidden) closeDrawer();
  });

  el.footTime.textContent = "页面加载时间 " + new Date().toLocaleString("zh-CN", { hour12: false });

  setInterval(tickCountdown, 1000);
  setInterval(function () {
    if (state.data) {
      var target = new Date(String(state.data.nextSync || "").replace(/-/g, "/")).getTime();
      if (target && Date.now() > target + 5000) load();
    }
  }, 60000);

  load();
})();
