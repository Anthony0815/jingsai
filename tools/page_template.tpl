<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>辽宁省创新创业大赛 · 官方通知聚合</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="topbar">
  <div class="wrap topbar-inner">
    <div class="brand">
      <div class="logo">辽</div>
      <div class="brand-text">
        <h1>辽宁省创新创业大赛 <span>官方通知聚合</span></h1>
        <p>省市教育厅与省级双创平台公开页面 · 每日 08:00 自动同步 · 标题与链接均保持官方原文</p>
      </div>
    </div>
    <div class="topbar-actions">
      <span class="refresh-hint" id="refreshHint" aria-live="polite"></span>
      <a class="btn ghost" id="platformLink" href="https://cxcy.upln.cn/" target="_blank" rel="noopener noreferrer">
        辽宁省双创平台 ↗
      </a>
      <button class="btn primary" id="refreshBtn" type="button" title="立即抓取官方页面并刷新本页">立即更新</button>
    </div>
  </div>
</header>

<main class="wrap">
  <section class="statusbar">
    <div class="stat">
      <span class="stat-label">最近同步</span>
      <strong id="lastSync">—</strong>
    </div>
    <div class="stat">
      <span class="stat-label">下次自动同步</span>
      <strong id="nextSync">—</strong>
      <em id="countdown" class="countdown"></em>
    </div>
    <div class="stat">
      <span class="stat-label">官方条目</span>
      <strong><span id="totalCount">0</span> 条</strong>
      <em id="newCount" class="newcount"></em>
    </div>
    <div class="stat">
      <span class="stat-label">双创平台连通</span>
      <strong id="platformState" class="state">检测中…</strong>
    </div>
  </section>

  <div class="layout">
    <section class="main-col">
      <div class="toolbar">
        <nav class="tabs" id="tabs" aria-label="频道筛选">
          <button class="tab active" data-tab="all" type="button">全部 <span class="num" data-num="all">0</span></button>
          <button class="tab" data-tab="cxcy" type="button">创新创业 <span class="num" data-num="cxcy">0</span></button>
          <button class="tab" data-tab="tournament" type="button">大赛活动 <span class="num" data-num="tournament">0</span></button>
          <button class="tab" data-tab="upln" type="button">省双创竞赛 <span class="num" data-num="upln">0</span></button>
          <button class="tab" data-tab="dlu" type="button">大连大学竞赛 <span class="num" data-num="dlu">0</span></button>
          <button class="tab" data-tab="zxtz" type="button">省厅通知</button>
          <button class="tab" data-tab="gsgg" type="button">公示公告</button>
          <button class="tab" data-tab="lnut" type="button">高校竞赛通知</button>
        </nav>
        <div class="search">
          <input id="searchInput" type="search" placeholder="搜索标题，如「选拔赛」" autocomplete="off">
        </div>
      </div>

      <ul class="notice-list" id="noticeList">
        <li class="skeleton"></li>
        <li class="skeleton"></li>
        <li class="skeleton"></li>
      </ul>
      <p class="empty" id="emptyTip" hidden>没有匹配的通知，换个关键词或频道试试。</p>
    </section>

    <aside class="side-col">
      <div class="card">
        <h2>官方入口</h2>
        <p class="card-sub">点击直达官方页面，报名与评审以官方系统为准。</p>
        <ul class="link-list" id="officialLinks"></ul>
      </div>
      <div class="card">
        <h2>数据来源</h2>
        <p class="card-sub">全部内容实时抓取自官方公开页面，不转载、不改写标题。</p>
        <ul class="source-list" id="sourceList"></ul>
      </div>
      <div class="card hint">
        <h2>同步说明</h2>
        <p>云端每天 <b id="syncHour">08:00</b> 自动抓取一次官方页面；点右上角「<b>立即更新</b>」可当场重新抓取，无需等待。</p>
        <p>抓取失败时该来源会保留上一次的内容并标记「沿用缓存」，不会出现编造条目。</p>
      </div>
    </aside>
  </div>
</main>

<footer class="footer wrap">
  <span>内容版权归原作者所有 · 本站仅做官方公开信息的聚合展示</span>
  <span id="footTime"></span>
</footer>

<div class="drawer-mask" id="drawerMask" hidden></div>
<section class="drawer" id="drawer" hidden aria-modal="true" role="dialog">
  <header class="drawer-head">
    <div>
      <h2 id="drawerTitle">通知原文</h2>
      <p class="drawer-meta" id="drawerMeta"></p>
    </div>
    <button class="icon-btn" id="drawerClose" type="button" aria-label="关闭">×</button>
  </header>
  <div class="drawer-body" id="drawerBody"></div>
  <footer class="drawer-foot">
    <a class="btn primary" id="drawerOpen" href="#" target="_blank" rel="noopener noreferrer">打开官方原文 ↗</a>
    <span class="drawer-note" id="drawerNote">正文由官方页面实时提取，仅作阅读预览，最终以官方原文为准。</span>
  </footer>
</section>

<script src="app.js"></script>
<!-- Cloudflare Web Analytics -->
<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "60c4770755e144ec9b2f520e89c4b863"}'></script>
<!-- End Cloudflare Web Analytics -->
</body>
</html>
