(function () {
  "use strict";

  var EMBED = window.__EMBEDDED_DATA__ || null;

  var state = {
    data: null,
    tab: "all",
    keyword: "",
    timer: null,
    busy: false
  };

  var el = {
    list: document.getElementById("noticeList"),
    empty: document.getElementById("emptyTip"),
    soon: document.getElementById("soon"),
    soonList: document.getElementById("soonList"),
    tabs: document.getElementById("tabs"),
    search: document.getElementById("searchInput"),
    refresh: document.getElementById("refreshBtn"),
    hint: document.getElementById("refreshHint"),
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
    "高校竞赛通知": "cxcy",
    "省双创竞赛": "upln",
    "大连大学竞赛通知": "dlu"
  };

  /* ------------------------------------------------ 浏览器端实时抓取配置 */
  // 公开 CORS 代理：官方站点不允许跨域读取，经由代理取回原始 HTML。
  // 这些免费代理偶尔会限流/宕机，所以准备多个，按顺序自动切换。
  var PROXIES = [
    function (u) { return "https://api.cors.lol/?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.allorigins.win/raw?url=" + encodeURIComponent(u); },
    function (u) { return "https://api.codetabs.com/v1/proxy/?quest=" + encodeURIComponent(u); }
  ];
  var PROXY_GOOD = 0;   // 记住上一次成功的代理，下次优先用

  var LIVE_SOURCES = [
    { key: "zxtz", name: "辽宁省教育厅 · 最新通知", category: "通知公告",
      url: "https://jyt.ln.gov.cn/jyt/gk/zxtz/index.shtml" },
    { key: "gsgg", name: "辽宁省教育厅 · 公示公告", category: "公示公告",
      url: "https://jyt.ln.gov.cn/jyt/gk/gsgg/index.shtml" },
    { key: "jyyw", name: "辽宁省教育厅 · 教育要闻", category: "赛事动态",
      url: "https://jyt.ln.gov.cn/jyt/jyzx/jyyw/index.shtml", filter: "race" },
    { key: "lnut", name: "辽宁工业大学 · 竞赛通知", category: "高校竞赛通知",
      url: "https://cxcy.lnut.edu.cn/scjs/jstz.htm", parser: "li", forceCxcy: true,
      pages: ["https://cxcy.lnut.edu.cn/scjs/jstz/27.htm"] },
    { key: "dlu", name: "大连大学 · 创新创业竞赛", category: "大连大学竞赛通知",
      url: "https://cxcy.dlu.edu.cn/kcsj/cxcyjs.htm", parser: "tr", forceCxcy: true,
      pages: ["https://cxcy.dlu.edu.cn/zxzx/zytz.htm"] }
  ];

  var KW_CXCY = ["创新创业", "双创", "互联网+", "挑战杯", "大学生创业", "创新项目",
    "创业项目", "创新大赛", "创业大赛", "训练计划", "创客", "创业孵化",
    "创新方法", "科技成果转化"];
  var KW_RACE = ["大赛", "竞赛", "赛事", "选拔赛", "赛区", "决赛", "初赛", "复赛",
    "路演", "获奖名单", "评审", "参赛", "赛", "评奖", "颁奖"];
  var SKIP_HINTS = ["无障碍", "网站地图", "返回", "更多", "登录", "注册", "首页"];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function pad(n) { return n < 10 ? "0" + n : "" + n; }

  function shortDay(v) {
    // 2026-11-01 00:00:00 -> 11-01
    var s = String(v || "");
    return s.length >= 10 ? s.slice(5, 10) : s;
  }

  function stateClass(s) {
    if (s === "报名中") return "st-live";
    if (s === "即将开始") return "st-soon";
    return "st-end";
  }

  /* ---------------------------------------------------- 报名截止相关 */
  function daysLeft(deadline) {
    if (!deadline) return null;
    var p = String(deadline).split("-");
    if (p.length !== 3) return null;
    var target = new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
    var n = new Date();
    var today = new Date(n.getFullYear(), n.getMonth(), n.getDate());
    if (isNaN(target.getTime())) return null;
    return Math.round((target - today) / 86400000);
  }

  function deadlineBadge(it) {
    var d = daysLeft(it.deadline);
    if (d === null) return "";
    if (d < 0) return '<span class="badge dd dd-end">已截止</span>';
    if (d === 0) return '<span class="badge dd dd-hot">今天截止</span>';
    if (d <= 3) return '<span class="badge dd dd-hot">剩 ' + d + " 天</span>";
    if (d <= 7) return '<span class="badge dd dd-warn">剩 ' + d + " 天</span>";
    return '<span class="badge dd">' + esc(shortDay(it.deadline)) + " 截止</span>";
  }

  function renderSoon() {
    if (!el.soon) return;
    var items = (state.data && state.data.items) || [];
    var soon = items.filter(function (it) {
      var d = daysLeft(it.deadline);
      return d !== null && d >= 0 && d <= 7;
    }).sort(function (a, b) {
      return String(a.deadline) < String(b.deadline) ? -1 : 1;
    });

    if (!soon.length) {
      el.soon.hidden = true;
      el.soonList.innerHTML = "";
      return;
    }

    el.soon.hidden = false;
    el.soonList.innerHTML = soon.map(function (it) {
      var d = daysLeft(it.deadline);
      var cls = d <= 3 ? "dd-hot" : "dd-warn";
      var tip = d === 0 ? "今天截止" : "剩 " + d + " 天";
      return '<li class="soon-item" data-url="' + esc(it.url) + '" data-id="' + esc(it.id) + '" tabindex="0">' +
        '<span class="badge dd ' + cls + '">' + tip + "</span>" +
        '<strong class="soon-title">' + esc(it.title) + "</strong>" +
        '<small class="soon-meta">' + esc(shortDay(it.deadline)) + " 截止 · " + esc(it.source) + "</small>" +
        "</li>";
    }).join("");
  }

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
    if (tab === "upln" && item.sourceKey !== "upln") return false;
    if (tab === "dlu" && item.sourceKey !== "dlu") return false;
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
      if (it.state) badges.push('<span class="badge st ' + stateClass(it.state) + '">' + esc(it.state) + "</span>");
      var dd = it.deadline ? deadlineBadge(it) : "";
      if (dd) badges.push(dd);
      if (it.isNew) badges.push('<span class="badge fresh">新</span>');

      var tags = (it.tags || []).filter(function (t) {
        return t.length > 1 && t !== it.state;
      }).slice(0, 2).map(function (t) {
        return '<span class="badge">' + esc(t) + "</span>";
      }).join("");

      var meta = "<span>" + esc(it.date || "日期以官方页面为准") + "</span>" +
        "<span>" + esc(it.source) + "</span>";
      if (it.signupStart && it.signupEnd) {
        meta += "<span>报名 " + esc(shortDay(it.signupStart)) + " 至 " + esc(shortDay(it.signupEnd)) + "</span>";
      }

      return '<li class="notice" data-url="' + esc(it.url) + '" data-id="' + esc(it.id) + '" tabindex="0">' +
        '<div class="notice-top">' + badges.join("") + tags + "</div>" +
        "<h3>" + esc(it.title) + "</h3>" +
        '<div class="notice-meta">' + meta + "</div>" +
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
    var nums = { all: items.length, cxcy: c.cxcy || 0, tournament: c.tournament || 0,
      upln: c.upln || 0, dlu: c.dlu || 0 };
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
      if (s.status === "stale") {
        label = "沿用缓存 " + (s.count || 0) + " 条";
        cls = "s-stale";
      } else if (s.status !== "ok") {
        label = "抓取失败";
        cls = "s-bad";
      }
      return '<li><span class="s-name" title="' + esc(s.name) + '">' + esc(s.name) + "</span>" +
        '<span class="' + cls + '">' + label + "</span></li>";
    }).join("");

    var p = state.data.platform || {};
    if (p.ok) {
      el.platform.textContent = "可访问";
      el.platform.className = "state ok";
      el.platform.title = (p.title || "") + " · 检测于 " + (p.checkedAt || "");
    } else if (p.status === "unknown") {
      el.platform.textContent = "未检测";
      el.platform.className = "state skip";
      el.platform.title = "本次运行环境网络无法完成检测，可直接点击上方入口访问";
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
    renderSoon();
    renderSide();
    tickCountdown();
    openFromQuery();
  }

  function load() {
    if (EMBED) {
      document.body.setAttribute("data-mode", "static");
      applyData(EMBED);
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

  /* ------------------------------------------------ 浏览器端实时抓取实现 */
  function pad2(n) { return n < 10 ? "0" + n : "" + n; }

  function nowStr() {
    var d = new Date();
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()) + " " +
      pad2(d.getHours()) + ":" + pad2(d.getMinutes()) + ":" + pad2(d.getSeconds());
  }

  function nextSyncStr() {
    // 云端每小时检查一次：下一次整点
    var d = new Date();
    var t = new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours() + 1, 0, 0, 0);
    return t.getFullYear() + "-" + pad2(t.getMonth() + 1) + "-" + pad2(t.getDate()) + " " +
      pad2(t.getHours()) + ":" + pad2(t.getMinutes()) + ":" + pad2(t.getSeconds());
  }

  function setHint(text) {
    if (el.hint) el.hint.textContent = text || "";
  }

  // 通过公开代理取回官方页面：按顺序试多个代理，全部失败再整体重试，最多 rounds 轮
  function viaProxy(url, tries) {
    var rounds = Math.max(1, tries || 1);

    function oneRound() {
      var order = [];
      for (var i = 0; i < PROXIES.length; i++) {
        order.push((PROXY_GOOD + i) % PROXIES.length);
      }
      function step(k) {
        if (k >= order.length) {
          return Promise.reject(new Error("所有代理均不可用"));
        }
        var idx = order[k];
        return fetch(PROXIES[idx](url), { cache: "no-store" })
          .then(function (r) {
            if (!r.ok) throw new Error("HTTP " + r.status);
            return r.text();
          })
          .then(function (t) {
            if (!t || t.length < 500) throw new Error("空响应");
            PROXY_GOOD = idx;
            return t;
          })
          .catch(function (err) {
            return step(k + 1).catch(function () { throw err; });
          });
      }
      return step(0);
    }

    var p = oneRound();
    for (var r = 1; r < rounds; r++) {
      p = p.catch(function () {
        return new Promise(function (res) { setTimeout(res, 900); }).then(oneRound);
      });
    }
    return p;
  }

  function liveDate(text) {
    var m = /(20\d{2})[-\/年]?(\d{2})[-\/月]?(\d{2})/.exec(text || "");
    if (!m) return "";
    var mo = +m[2], day = +m[3];
    if (mo < 1 || mo > 12 || day < 1 || day > 31) return "";
    return m[1] + "-" + m[2] + "-" + m[3];
  }

  function liveAccept(title) {
    if (!title || title.length < 6) return false;
    return !SKIP_HINTS.some(function (h) { return title.indexOf(h) !== -1; });
  }

  function liveTags(title) {
    var cxcy = KW_CXCY.filter(function (k) { return title.indexOf(k) !== -1; });
    var race = KW_RACE.filter(function (k) { return title.indexOf(k) !== -1; });
    var tags = cxcy.slice(0, 2).concat(race.slice(0, 2)).filter(function (v, i, arr) {
      return arr.indexOf(v) === i;
    });
    return { cxcy: cxcy, tags: tags };
  }

  function mkItem(src, href, title, date) {
    var tg = liveTags(title);
    return {
      id: href, title: title, url: href, date: date,
      sourceKey: src.key, source: src.name, category: src.category,
      cxcy: !!(tg.cxcy.length || src.forceCxcy),
      tournament: !!(tg.cxcy.length || tg.tags.length),
      tags: tg.tags
    };
  }

  function scrapeList(html, src) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    var out = [];

    function push(href, title, date) {
      if (!liveAccept(title) || !date) return;
      var abs = href;
      try { abs = new URL(href, src.url).href; } catch (e) { return; }
      var tg = liveTags(title);
      if (src.filter === "race" && !tg.cxcy.length && !tg.tags.length) return;
      out.push(mkItem(src, abs, title, date));
    }

    if (src.parser === "li") {
      Array.prototype.forEach.call(doc.querySelectorAll("li"), function (li) {
        var a = li.querySelector("a[href]");
        if (!a) return;
        var href = a.getAttribute("href") || "";
        if (!/info\/\d+\/\d+\.s?html?$/.test(href)) return;
        var title = (a.getAttribute("title") || a.textContent || "").replace(/\s+/g, " ").trim();
        push(href, title, liveDate(li.textContent) || liveDate(href));
      });
    } else if (src.parser === "tr") {
      Array.prototype.forEach.call(doc.querySelectorAll("tr"), function (tr) {
        var a = tr.querySelector("a[href]");
        if (!a) return;
        var href = a.getAttribute("href") || "";
        if (!/info\/\d+\/\d+\.s?html?$/.test(href)) return;
        var title = (a.getAttribute("title") || a.textContent || "").replace(/\s+/g, " ").trim();
        push(href, title, liveDate(tr.textContent) || liveDate(href));
      });
    } else {
      Array.prototype.forEach.call(doc.querySelectorAll("a[href]"), function (a) {
        var href = a.getAttribute("href") || "";
        if (!/\/\d{6,}\/?(?:index\.s?html?)?$/.test(href)) return;
        var title = (a.getAttribute("title") || a.textContent || "").replace(/\s+/g, " ").trim();
        var near = a.parentElement ? a.parentElement.textContent : "";
        push(href, title, liveDate(href) || liveDate(near));
      });
    }
    return out;
  }

  function scrapeSource(src) {
    var pages = [src.url].concat(src.pages || []);
    return Promise.all(pages.map(function (p) {
      return viaProxy(p).then(function (html) { return scrapeList(html, src); })
        .catch(function () { return []; });
    })).then(function (chunks) {
      var items = chunks.reduce(function (a, b) { return a.concat(b); }, []);
      if (!items.length) throw new Error("no items");
      return items;
    });
  }

  function liveUpdate() {
    if (state.busy) return;
    state.busy = true;
    var label = el.refresh ? el.refresh.textContent : "";
    if (el.refresh) { el.refresh.disabled = true; el.refresh.textContent = "更新中…"; }
    setHint("正在抓取官方页面…");

    function finish(msg) {
      state.busy = false;
      if (el.refresh) { el.refresh.disabled = false; el.refresh.textContent = label || "立即更新"; }
      setHint(msg);
    }

    var jobs = LIVE_SOURCES.map(function (src) {
      return scrapeSource(src).then(function (items) {
        return { src: src, items: items };
      }).catch(function () {
        return { src: src, items: null };
      });
    });

    Promise.all(jobs).then(function (results) {
      var prev = (state.data && state.data.items) || [];
      var seenUrl = {};
      prev.forEach(function (it) { seenUrl[it.url] = it; });

      var merged = [], stats = [], liveOk = 0;
      results.forEach(function (r) {
        if (r.items && r.items.length) {
          liveOk += 1;
          merged = merged.concat(r.items);
          stats.push({ key: r.src.key, name: r.src.name, status: "ok", count: r.items.length });
        } else {
          var cached = prev.filter(function (it) { return it.sourceKey === r.src.key; })
            .map(function (it) { return Object.assign({}, it, { stale: true }); });
          merged = merged.concat(cached);
          stats.push({
            key: r.src.key, name: r.src.name,
            status: cached.length ? "stale" : "fail", count: cached.length,
            error: "浏览器实时抓取失败"
          });
        }
      });

      // 省平台接口禁止跨域，沿用云端发布时抓到的竞赛条目
      var upln = prev.filter(function (it) { return it.sourceKey === "upln"; })
        .map(function (it) { return Object.assign({}, it, { stale: true }); });
      if (upln.length) {
        merged = merged.concat(upln);
        stats.push({
          key: "upln", name: "辽宁省双创平台 · 竞赛大厅",
          status: "stale", count: upln.length, error: "接口禁止跨域，显示上次云端结果"
        });
      }

      var seen = {}, items = [];
      merged.forEach(function (it) {
        if (seen[it.url]) return;
        seen[it.url] = 1;
        items.push(it);
      });
      items.sort(function (a, b) {
        return String(b.date || "").localeCompare(String(a.date || "")) ||
          String(b.title || "").localeCompare(String(a.title || ""));
      });
      items.forEach(function (it) { it.isNew = !seenUrl[it.url]; });

      var counts = {
        total: items.length,
        cxcy: items.filter(function (x) { return x.cxcy; }).length,
        tournament: items.filter(function (x) { return x.tournament; }).length,
        upln: items.filter(function (x) { return x.sourceKey === "upln"; }).length,
        new: items.filter(function (x) { return x.isNew; }).length
      };

      var snap = Object.assign({}, state.data || {}, {
        generatedAt: nowStr(),
        nextSync: nextSyncStr(),
        items: items,
        counts: counts,
        sources: stats,
        platform: { ok: false, status: "unknown", name: "辽宁省大学生创新创业管理共享平台", url: "https://cxcy.upln.cn/" },
        liveUpdated: true
      });
      applyData(snap);

      if (liveOk === LIVE_SOURCES.length) {
        finish("已更新 · 实时抓取 " + items.length + " 条");
      } else if (liveOk > 0) {
        finish("已更新 · " + liveOk + "/" + LIVE_SOURCES.length + " 个来源实时抓取成功");
      } else {
        finish("实时抓取失败：公共代理暂不可用，已保留上次结果");
      }
    }).catch(function () {
      finish("更新失败：公共代理暂时不可用（官方站禁止跨域），稍后重试即可");
    });
  }

  function doRefresh() {
    if (!el.refresh) return;
    if (!EMBED) {
      // 本地服务模式：直接调用后端刷新（会真正抓取并落盘）
      el.refresh.disabled = true;
      el.refresh.textContent = "更新中…";
      setHint("");
      return fetch("/api/refresh", { cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(function (res) { if (res.ok) applyData(res.data); })
        .catch(function () {})
        .then(function () {
          el.refresh.disabled = false;
          el.refresh.textContent = "立即更新";
        });
    }
    liveUpdate();
  }

  /* ------------------------------------------------------------ drawer */
  var NOISE = /^(字号|打印|关闭|分享|扫一扫|字体|【|打印本页|返回顶部)[:：]?/;

  var DRAWER_NOTE = "正文由官方页面实时提取，仅作阅读预览，最终以官方原文为准。";

  function drawerUpln(item) {
    var url = item.url || "https://cxcy.upln.cn/";
    el.drawerBody.innerHTML = [
      '<div class="xnote">',
      '  <h4>该竞赛详情需到双创平台查看</h4>',
      '  <p>辽宁省大学生创新创业管理共享平台（省双创平台）与本页服务器跨域不兼容：',
      '     该平台的接口拒绝浏览器跨域请求，因此这里无法直接显示大赛正文。</p>',
      '  <p>大赛名称、报名时间等信息来自平台公开的竞赛大厅，与官方一致；',
      '     完整通知、报名入口与评审结果，请前往官方平台查看。</p>',
      '  <a class="xbtn" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">点击前往双创平台查看详情 ↗</a>',
      '  <p class="xnote-url">' + esc(url) + '</p>',
      '</div>'
    ].join("");
  }

  function drawerDlu(item) {
    var url = item.url || "https://cxcy.dlu.edu.cn/";
    var school = item.source || "大连大学 · 创新创业竞赛";
    el.drawerBody.innerHTML = [
      '<div class="xnote">',
      '  <h4>该通知详情需到大连大学官网查看</h4>',
      '  <p>正文预览暂时读不到：' + esc(school) + ' 的网站与本页不在同一个域，',
      '     且只对校园 / 国内网络开放，浏览器跨域请求被拦截、公共代理读取也会超时。</p>',
      '  <p>标题、发布日期与报名截止时间均取自该校官网公开列表，与官方一致；',
      '     完整通知与附件，请点下方按钮前往学校官网原文。</p>',
      '  <a class="xbtn" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">打开官方原文 ↗</a>',
      '  <p class="xnote-url">' + esc(url) + '</p>',
      '</div>'
    ].join("");
  }

  function drawerFromProxy(item) {
    viaProxy(item.url, 2).then(function (html) {
      var doc = new DOMParser().parseFromString(html, "text/html");
      Array.prototype.forEach.call(doc.querySelectorAll("script,style,nav,header,footer"), function (n) {
        n.parentNode && n.parentNode.removeChild(n);
      });
      var texts = Array.prototype.map.call(doc.querySelectorAll("p"), function (p) {
        return (p.textContent || "").replace(/\s+/g, " ").trim();
      }).filter(function (t) {
        return t.length > 10 && !NOISE.test(t);
      });
      if (!texts.length) throw new Error("empty");
      el.drawerBody.innerHTML = texts.slice(0, 80).map(function (t) {
        return "<p>" + esc(t) + "</p>";
      }).join("");
    }).catch(function () {
      el.drawerBody.innerHTML = '<p>正文预览暂时读不到（代理通道繁忙），请点击下方「打开官方原文 ↗」查看官方全文。</p>';
    });
  }

  function openDrawer(item) {
    var title = item.title;
    el.drawerTitle.textContent = title;
    el.drawerMeta.textContent = [item.date, item.source].filter(Boolean).join(" · ");
    el.drawerOpen.href = item.url;
    el.drawer.hidden = false;
    el.mask.hidden = false;
    document.body.style.overflow = "hidden";

    var note = document.getElementById("drawerNote");
    if (note) note.textContent = DRAWER_NOTE;

    if (item.sourceKey === "upln") {
      if (note) note.textContent = "该平台接口禁止跨域，站内无法预览正文，请前往官方平台查看。";
      drawerUpln(item);
      return;
    }

    if (item.sourceKey === "dlu") {
      if (note) note.textContent = "正文预览暂时读不到（该站不允许跨域，代理也超时），请点下方「打开官方原文」。";
      drawerDlu(item);
      return;
    }

    el.drawerBody.innerHTML = '<p class="loading-line">正在从官方页面读取原文…</p>';

    if (EMBED) {
      drawerFromProxy(item);
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
  function bindSoon() {
    if (!el.soonList) return;
    function open(e) {
      var li = e.target.closest(".soon-item");
      if (!li || !state.data) return;
      var item = (state.data.items || []).filter(function (x) { return x.id === li.dataset.id; })[0];
      if (item) openDrawer(item);
    }
    el.soonList.addEventListener("click", open);
    el.soonList.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      e.preventDefault();
      open(e);
    });
  }
  bindSoon();

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

  // 支持 ?refresh=1 打开即抓取最新（便于分享「打开就是最新」的链接）
  if (/[?&]refresh=1\b/.test(location.search) && el.refresh) {
    setTimeout(doRefresh, 400);
  }
})();
