"use strict";
(() => {
  const data = window.NEURONAV_DEMO;
  const content = document.querySelector("#stage-content");
  const title = document.querySelector("#step-title");
  const eyebrow = document.querySelector("#step-eyebrow");
  const description = document.querySelector("#step-description");
  const escape = (value) => String(value).replace(/[&<>"']/g, (character) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character]));
  const statusLabels = {
    RECRUITING: "正在招募",
    ACTIVE_NOT_RECRUITING: "进行中 · 不再招募",
    NOT_YET_RECRUITING: "尚未招募",
    ENROLLING_BY_INVITATION: "邀请入组"
  };
  const percent = (value) => (100 * value).toFixed(value === 1 ? 0 : 1) + "%";
  const detailCell = (label, value) => '<div class="detail-cell"><span>' + escape(label) + "</span><strong>" + escape(value) + "</strong></div>";
  const evidenceRow = (label, field, outcome, caution = false) =>
    '<div class="evidence-line"><span>' + escape(label) + "</span><code>" + escape(field) +
    '</code><b class="' + (caution ? "caution" : "") + '">' + escape(outcome) + "</b></div>";

  if (data && content) {
    const cards = () => data.candidates.map((candidate) => {
      const amber = candidate.overall_status !== "RECRUITING";
      return '<article class="trial-card"><span class="trial-rank">' + String(candidate.rank).padStart(2, "0") +
        '</span><div><a class="trial-title" href="' + escape(candidate.source_url) + '" target="_blank" rel="noopener">' +
        escape(candidate.title) + ' <span aria-hidden="true">↗</span></a><div class="trial-meta"><code>' +
        escape(candidate.nct_id) + '</code><span>·</span><span class="status-badge ' + (amber ? "amber" : "") + '">' +
        escape(statusLabels[candidate.overall_status] || candidate.overall_status) + '</span></div></div><div class="trial-score">' +
        candidate.base_score.toFixed(3) + "<small>排序分数</small></div></article>";
    }).join("");
    const steps = [
      {
        label: "PROFILE INTAKE",
        title: "只保留导航需要的信息。",
        description: "这是一份合成研究画像。字段与公开报告一致，不包含参与者身份信息。",
        render: () => '<div class="stage-grid">' + detailCell("目标疾病", data.profile.condition) +
          detailCell("年龄", data.profile.age + " 岁") + detailCell("登记性别类别", "female · 女性") +
          detailCell("国家 / 地区", data.profile.country + " · 巴西") +
          '</div><p class="stage-note">用途：探索较低登记覆盖场景下的候选排序，而非对真实个人提供医疗建议。</p>'
      },
      {
        label: "STRUCTURED SCREENING",
        title: "把每个条件拆开检查。",
        description: "读取固定登记快照；有限的结构化字段检查后，保留尚无硬排除的候选。",
        render: () => '<div class="stage-metric"><div><strong>' + data.records.toLocaleString("en-US") +
          '</strong><span>读取的登记记录</span></div><div><strong>' + data.screened_candidates.toLocaleString("en-US") +
          '</strong><span>未触发硬排除的候选</span></div></div>' +
          '<p class="stage-note">检查疾病、年龄、登记性别类别、研究状态和国家信息。v0.1 仍纳入“进行中但不再招募”的记录，因此通过筛查不表示可报名。</p>' +
          evidenceRow("待确认", "eligibility_text", "人工复核", true)
      },
      {
        label: "SENSITIVITY ANALYSIS",
        title: "改变权重，观察排名变化。",
        description: "使用固定随机种子 42，抽样 2,000 组权重，计算候选进入前十的频率。",
        render: () => data.candidates.map(candidate => evidenceRow("基础排名 " + candidate.rank, candidate.nct_id, percent(candidate.top_k_probability))).join("") +
          '<p class="stage-note">这些数值表示排序对权重变化的敏感程度。100% 也不意味着一定符合入组条件，更不是治疗成功概率。</p>'
      },
      {
        label: "EVIDENCE AUDIT",
        title: "每条结论，都回到来源字段。",
        description: "对已保存报告中的 " + data.audit_count + " 项候选执行来源字段、分数范围与人工复核标记检查。",
        render: () => evidenceRow("疾病字段", "conditions", "可追溯") +
          evidenceRow("年龄范围", "minimum_age_years / maximum_age_years", "可追溯") +
          evidenceRow("登记地点", "countries", "可追溯") +
          evidenceRow("复杂入排条件", "eligibility_text", "待人工判断", true) +
          '<p class="stage-note">证据审核验证输出结构与字段引用；不表示已完成医学审查。</p>'
      },
      {
        label: "NAVIGATION REPORT",
        title: "候选报告，一眼可追溯。",
        description: "以下为已保存报告的前三项。排序分数表示导航相关性，招募状态与入组条件仍需单独确认。",
        render: cards
      }
    ];
    function showStep(index) {
      const step = steps[index];
      title.textContent = step.title;
      eyebrow.textContent = step.label;
      description.textContent = step.description;
      content.innerHTML = step.render();
      document.querySelectorAll("[data-step]").forEach(button => {
        const active = Number(button.dataset.step) === index;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
      });
    }
    document.querySelectorAll("[data-step]").forEach(button => {
      button.addEventListener("click", () => showStep(Number(button.dataset.step)));
    });
    showStep(4);
  }

  document.querySelectorAll("[data-result]").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-result]").forEach(tab => {
        const active = tab === button;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-pressed", String(active));
        document.getElementById(tab.dataset.result + "-view").hidden = !active;
      });
    });
  });

  let toastTimer;
  function notify(message) {
    const status = document.getElementById("copy-status");
    status.textContent = message;
    status.classList.add("visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => status.classList.remove("visible"), 2600);
  }
  document.querySelectorAll("[data-copy-target]").forEach(button => {
    button.addEventListener("click", async () => {
      const text = document.getElementById(button.dataset.copyTarget).textContent;
      let copied = false;
      try {
        await navigator.clipboard.writeText(text);
        copied = true;
      } catch {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.cssText = "position:fixed;left:-9999px;top:0";
        document.body.append(textarea);
        textarea.select();
        copied = document.execCommand("copy");
        textarea.remove();
        button.focus();
      }
      notify(copied ? "命令已复制，按系统选择激活命令后运行。" : "浏览器未允许复制，请在命令区手动选择并复制。");
    });
  });
})();
