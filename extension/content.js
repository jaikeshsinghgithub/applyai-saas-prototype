// ApplyAI Content Script v3 — FULL AUTO-APPLY (Fill + Submit)
// Supports: LinkedIn Easy Apply, Naukri, Foundit, Indeed

(function () {
  'use strict';

  let userProfile = null;
  let autoSubmitEnabled = false;
  const HOST = window.location.hostname;

  chrome.storage.local.get(['applyai_profile', 'applyai_settings'], (data) => {
    userProfile = data.applyai_profile || null;
    const settings = data.applyai_settings || {};
    autoSubmitEnabled = settings.auto_submit !== false; // default: true

    setTimeout(() => {
      if (HOST.includes('linkedin')) observeLinkedInApply();
      if (HOST.includes('naukri')) observeNaukriApply();
      if (HOST.includes('foundit')) observeFounditApply();
    }, 2000);
  });

  // Listen for fill command from popup
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'fill_form') {
      chrome.storage.local.get(['applyai_profile', 'applyai_settings'], (data) => {
        userProfile = data.applyai_profile;
        autoSubmitEnabled = (data.applyai_settings || {}).auto_submit !== false;
        if (!userProfile) {
          showToast('⚠️ Set up your profile in the extension first!', 'warn');
          sendResponse({ success: false, filled: 0 });
          return;
        }
        const filled = fillForms();
        sendResponse({ success: filled > 0, filled });
      });
      return true;
    }
    if (msg.action === 'full_apply') {
      chrome.storage.local.get(['applyai_profile', 'applyai_settings'], (data) => {
        userProfile = data.applyai_profile;
        autoSubmitEnabled = true; // force submit
        if (!userProfile) { sendResponse({ success: false }); return; }
        fillForms();
        setTimeout(() => clickSubmit(), 1200);
        sendResponse({ success: true });
      });
      return true;
    }
  });

  // ─── DISPATCH ───────────────────────────────────────────────
  function fillForms() {
    if (!userProfile) return 0;
    try {
      if (HOST.includes('naukri.com')) return fillNaukri();
      if (HOST.includes('linkedin.com')) return fillLinkedIn();
      if (HOST.includes('foundit.in')) return fillFoundit();
      if (HOST.includes('indeed')) return fillIndeed();
      if (HOST.includes('internshala')) return fillInternshala();
      return fillGeneric();
    } catch (e) {
      console.error('[ApplyAI]', e);
      showToast('⚠️ Error filling form', 'warn');
      return 0;
    }
  }

  // ─── LINKEDIN EASY APPLY ─────────────────────────────────────
  function fillLinkedIn() {
    const p = userProfile;
    let filled = 0;
    const [first, ...rest] = (p.name || '').split(' ');
    const last = rest.join(' ') || 'User';

    const map = [
      { sels: ['input[id*="firstName"]', 'input[aria-label*="First name" i]', 'input[placeholder*="First name" i]'], val: first },
      { sels: ['input[id*="lastName"]', 'input[aria-label*="Last name" i]', 'input[placeholder*="Last name" i]'], val: last },
      { sels: ['input[id*="phoneNumber"]', 'input[name*="phone"]', 'input[type="tel"]', 'input[aria-label*="Phone" i]'], val: p.phone },
      { sels: ['input[id*="city"]', 'input[name*="city"]', 'input[aria-label*="City" i]', 'input[placeholder*="City" i]'], val: p.location },
    ];
    for (const { sels, val } of map) filled += fillFirst(sels, val);

    // Textareas (cover message / summary)
    document.querySelectorAll('textarea').forEach(ta => {
      const lbl = getLabel(ta).toLowerCase();
      if (lbl.includes('summary') || lbl.includes('cover') || lbl.includes('message') || lbl.includes('additional')) {
        setVal(ta, buildCoverSnippet(p));
        filled++;
      }
    });

    // Fill dropdowns: Yes/No screener questions (answer "Yes" by default)
    document.querySelectorAll('select, fieldset').forEach(el => {
      const lbl = getLabel(el).toLowerCase();
      if (lbl.includes('authorized') || lbl.includes('eligible') || lbl.includes('agree') || lbl.includes('legally')) {
        const yesOpt = el.querySelector('option[value="Yes"],option[value="true"],option[value="1"]');
        if (yesOpt) { setVal(el, yesOpt.value); filled++; }
      }
      if (lbl.includes('experience') || lbl.includes('years')) {
        const exp = parseInt(p.experience) || 3;
        const opts = Array.from(el.querySelectorAll('option'));
        const match = opts.find(o => o.textContent.includes(String(exp)));
        if (match) { setVal(el, match.value); filled++; }
      }
    });

    if (filled === 0) filled += fillGeneric();
    showToast(`✅ Filled ${filled} fields on LinkedIn!`, 'success');

    if (autoSubmitEnabled) {
      setTimeout(() => handleLinkedInMultiStep(), 1500);
    }
    return filled;
  }

  // LinkedIn multi-step Easy Apply handler
  function handleLinkedInMultiStep() {
    let attempts = 0;
    const maxAttempts = 8;

    function step() {
      if (attempts++ >= maxAttempts) return;

      // Check for "Submit application" button first
      const submitBtn = findBtn(['Submit application', 'Submit Application', 'Submit']);
      if (submitBtn) {
        showToast('🚀 Submitting application...', 'info');
        setTimeout(() => {
          submitBtn.click();
          showToast('✅ ApplicationSubmitted on LinkedIn!', 'success');
          chrome.runtime.sendMessage({
            action: 'application_submitted',
            job_title: document.querySelector('.job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title')?.textContent?.trim() || 'LinkedIn Job',
            company: document.querySelector('.job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name a')?.textContent?.trim() || 'Company',
            portal: 'linkedin'
          });
        }, 600);
        return;
      }

      // "Next" or "Review" button — advance the form
      const nextBtn = findBtn(['Next', 'Continue', 'Review your application', 'Review']);
      if (nextBtn) {
        fillLinkedIn(); // fill any new fields
        setTimeout(() => {
          nextBtn.click();
          setTimeout(step, 1800); // wait for next step
        }, 800);
        return;
      }

      // "Easy Apply" button — start the flow
      const easyApplyBtn = findBtn(['Easy Apply', 'Apply']);
      if (easyApplyBtn) {
        easyApplyBtn.click();
        setTimeout(step, 1200);
        return;
      }

      setTimeout(step, 1000);
    }
    step();
  }

  // ─── NAUKRI ──────────────────────────────────────────────────
  function fillNaukri() {
    const p = userProfile;
    let filled = 0;

    const selectorMap = {
      '#name,[name="name"],[placeholder*="name" i]': p.name,
      '#email,[name="email"],[placeholder*="email" i]': p.email,
      '#mobile,[name="mobile"],[placeholder*="mobile" i],[placeholder*="phone" i]': p.phone,
      '[name="experience"],[placeholder*="experience" i],[id*="experience"]': p.experience,
      '[name="currentSalary"],[placeholder*="current salary" i]': p.currentSalary || '',
      '[name="expectedSalary"],[placeholder*="expected salary" i]': p.expectedSalary || '',
      '[name="noticePeriod"],[placeholder*="notice" i]': p.noticePeriod || '30',
      '[placeholder*="location" i],[placeholder*="city" i]': p.location,
    };

    for (const [sel, val] of Object.entries(selectorMap)) {
      if (!val) continue;
      try {
        document.querySelectorAll(sel).forEach(el => {
          if (el && !el.disabled && el.type !== 'hidden') { setVal(el, val); filled++; }
        });
      } catch (e) { }
    }

    if (filled === 0) filled += fillGeneric();
    showToast(`✅ Filled ${filled} fields on Naukri!`, 'success');

    if (autoSubmitEnabled) {
      setTimeout(() => {
        const submitBtn = findBtn(['Apply', 'Apply Now', 'Quick Apply', 'Submit', 'Send Application']);
        if (submitBtn) {
          showToast('🚀 Submitting on Naukri...', 'info');
          setTimeout(() => {
            submitBtn.click();
            showToast('✅ Applied on Naukri!', 'success');
            chrome.runtime.sendMessage({
              action: 'application_submitted',
              job_title: document.querySelector('.jd-header-title, h1.title')?.textContent?.trim() || 'Naukri Job',
              company: document.querySelector('.jd-header-comp-name, .comp-name')?.textContent?.trim() || 'Company',
              portal: 'naukri'
            });
          }, 600);
        } else {
          showToast('⚠️ Click Apply button to submit', 'warn');
        }
      }, 1200);
    }
    return filled;
  }

  // ─── FOUNDIT ─────────────────────────────────────────────────
  function fillFoundit() {
    const p = userProfile;
    let filled = 0;

    const selectorMap = {
      'input[name="name"],[placeholder*="name" i],[id*="name"]': p.name,
      'input[type="email"],[placeholder*="email" i]': p.email,
      'input[type="tel"],[placeholder*="phone" i],[placeholder*="mobile" i]': p.phone,
      'input[placeholder*="experience" i],[name*="experience"]': p.experience,
      'input[placeholder*="location" i],[placeholder*="city" i]': p.location,
      'input[placeholder*="salary" i],[name*="salary"]': p.expectedSalary || '',
    };

    for (const [sel, val] of Object.entries(selectorMap)) {
      if (!val) continue;
      try {
        document.querySelectorAll(sel).forEach(el => {
          if (el && !el.disabled) { setVal(el, val); filled++; }
        });
      } catch (e) { }
    }

    if (filled === 0) filled += fillGeneric();
    showToast(`✅ Filled ${filled} fields on Foundit!`, 'success');

    if (autoSubmitEnabled) {
      setTimeout(() => {
        const submitBtn = findBtn(['Apply', 'Apply Now', 'Quick Apply', 'Submit']);
        if (submitBtn) {
          showToast('🚀 Submitting on Foundit...', 'info');
          setTimeout(() => {
            submitBtn.click();
            showToast('✅ Applied on Foundit!', 'success');
            chrome.runtime.sendMessage({
              action: 'application_submitted',
              job_title: document.querySelector('h1, .job-title')?.textContent?.trim() || 'Foundit Job',
              company: document.querySelector('.company-name, .comp-name')?.textContent?.trim() || 'Company',
              portal: 'foundit'
            });
          }, 500);
        } else {
          showToast('⚠️ Click Apply to submit', 'warn');
        }
      }, 1200);
    }
    return filled;
  }

  // ─── INDEED ──────────────────────────────────────────────────
  function fillIndeed() {
    const p = userProfile;
    let filled = 0;
    const selectorMap = {
      '[name="applicant.name"],[id*="applicantName"],[aria-label*="name" i]': p.name,
      '[name="applicant.email"],[id*="email"],[aria-label*="email" i]': p.email,
      '[name="applicant.phoneNumber"],[id*="phone"],[aria-label*="phone" i]': p.phone,
    };
    for (const [sel, val] of Object.entries(selectorMap)) {
      try { document.querySelectorAll(sel).forEach(el => { setVal(el, val); filled++; }); } catch (e) { }
    }
    if (filled === 0) filled += fillGeneric();
    showToast(`✅ Filled ${filled} fields on Indeed!`, 'success');
    if (autoSubmitEnabled) {
      setTimeout(() => {
        const btn = findBtn(['Submit your application', 'Submit', 'Apply Now']);
        if (btn) { btn.click(); showToast('✅ Applied on Indeed!', 'success'); }
      }, 1000);
    }
    return filled;
  }

  // ─── INTERNSHALA ─────────────────────────────────────────────
  function fillInternshala() {
    const p = userProfile;
    let filled = 0;
    const selectorMap = {
      'input[name="name"],[placeholder*="name" i]': p.name,
      'input[name="email"],[type="email"]': p.email,
      'input[name="mobile"],[type="tel"]': p.phone,
    };
    for (const [sel, val] of Object.entries(selectorMap)) {
      try { document.querySelectorAll(sel).forEach(el => { setVal(el, val); filled++; }); } catch (e) { }
    }
    if (filled === 0) filled += fillGeneric();
    showToast(`✅ Filled ${filled} fields!`, 'success');
    if (autoSubmitEnabled) {
      setTimeout(() => {
        const btn = findBtn(['Submit', 'Apply']);
        if (btn) { btn.click(); showToast('✅ Applied on Internshala!', 'success'); }
      }, 1000);
    }
    return filled;
  }

  // ─── GENERIC ─────────────────────────────────────────────────
  function fillGeneric() {
    const p = userProfile;
    let filled = 0;
    document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="checkbox"]):not([type="radio"]), textarea').forEach(el => {
      if (el.disabled || el.readOnly || el.value) return;
      const ctx = [el.id, el.name, el.placeholder, el.getAttribute('aria-label')].join(' ').toLowerCase();
      let val = null;
      if (/first[\s_-]?name/.test(ctx)) val = (p.name || '').split(' ')[0];
      else if (/last[\s_-]?name/.test(ctx)) val = (p.name || '').split(' ').slice(1).join(' ') || 'User';
      else if (/\bname\b/.test(ctx) && !/company|org|school/.test(ctx)) val = p.name;
      else if (/\bemail\b/.test(ctx)) val = p.email;
      else if (/phone|mobile|contact/.test(ctx)) val = p.phone;
      else if (/\blocation|city\b/.test(ctx)) val = p.location;
      else if (/\bexperience|exp\b/.test(ctx)) val = p.experience;
      else if (/current.*salary/.test(ctx)) val = p.currentSalary || '';
      else if (/expected.*salary|desired/.test(ctx)) val = p.expectedSalary || '';
      else if (/notice[\s_-]?period/.test(ctx)) val = p.noticePeriod || '30';
      if (val) { setVal(el, val); filled++; }
    });
    return filled;
  }

  // ─── CLICK SUBMIT (generic) ───────────────────────────────────
  function clickSubmit() {
    const btn = findBtn(['Submit application', 'Submit Application', 'Submit', 'Apply Now', 'Apply', 'Send Application', 'Quick Apply']);
    if (btn) { btn.click(); return true; }
    return false;
  }

  // ─── OBSERVERS ───────────────────────────────────────────────
  function observeLinkedInApply() {
    const obs = new MutationObserver(() => {
      const modal = document.querySelector('.jobs-easy-apply-modal, [data-test-modal]');
      if (modal && !modal.dataset.applyaiFilled) {
        modal.dataset.applyaiFilled = '1';
        chrome.storage.local.get(['applyai_settings'], d => {
          autoSubmitEnabled = (d.applyai_settings || {}).auto_submit !== false;
        });
        setTimeout(() => {
          const f = fillLinkedIn();
          if (f > 0) showToast(`⚡ ApplyAI auto-filled ${f} fields`, 'info');
        }, 800);
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  function observeNaukriApply() {
    const obs = new MutationObserver(() => {
      const modal = document.querySelector('.apply-modal, .naukri-apply-widget, [class*="applyModal"]');
      if (modal && !modal.dataset.applyaiFilled) {
        modal.dataset.applyaiFilled = '1';
        setTimeout(() => fillNaukri(), 700);
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  function observeFounditApply() {
    const obs = new MutationObserver(() => {
      const modal = document.querySelector('[class*="applyModal"],[class*="quick-apply"],[class*="apply-modal"]');
      if (modal && !modal.dataset.applyaiFilled) {
        modal.dataset.applyaiFilled = '1';
        setTimeout(() => fillFoundit(), 700);
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  // ─── HELPERS ─────────────────────────────────────────────────
  function findBtn(labels) {
    const btns = Array.from(document.querySelectorAll('button, input[type="submit"], a[role="button"]'));
    for (const lbl of labels) {
      const found = btns.find(b =>
        b.textContent.trim().toLowerCase() === lbl.toLowerCase() ||
        b.value?.toLowerCase() === lbl.toLowerCase() ||
        b.getAttribute('aria-label')?.toLowerCase() === lbl.toLowerCase()
      );
      if (found && found.offsetParent && !found.disabled) return found;
    }
    return null;
  }

  function fillFirst(sels, value) {
    if (!value) return 0;
    for (const sel of sels) {
      try {
        const el = document.querySelector(sel);
        if (el && !el.disabled) { setVal(el, value); return 1; }
      } catch (e) { }
    }
    return 0;
  }

  function getLabel(el) {
    const id = el.id;
    if (id) {
      const lbl = document.querySelector(`label[for="${id}"]`);
      if (lbl) return lbl.textContent;
    }
    const aria = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || '';
    return aria || el.placeholder || el.name || '';
  }

  function buildCoverSnippet(p) {
    const skills = (p.skills || []).slice(0, 3).join(', ') || 'software development';
    return `I am a ${p.experience || '3'}-year experienced ${p.jobTitle || 'developer'} with expertise in ${skills}. I am excited about this opportunity and believe my background is a strong match. Please find my details attached.`;
  }

  function setVal(el, value) {
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    ['input', 'change', 'blur'].forEach(evt => el.dispatchEvent(new Event(evt, { bubbles: true })));
    el.style.outline = '2px solid rgba(99,102,241,.7)';
    setTimeout(() => el.style.outline = '', 3000);
  }

  function showToast(msg, type = 'success') {
    const old = document.getElementById('applyai-toast');
    if (old) old.remove();
    const colors = { success: '#10b981', warn: '#f59e0b', info: '#6366f1' };
    const toast = document.createElement('div');
    toast.id = 'applyai-toast';
    toast.style.cssText = `
      position:fixed;top:20px;right:20px;z-index:2147483647;
      background:#0d0d1a;border:1.5px solid ${colors[type] || colors.success};
      color:#f1f1ff;padding:14px 18px;border-radius:14px;
      font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;font-weight:500;
      box-shadow:0 8px 40px rgba(0,0,0,.7);display:flex;align-items:center;
      gap:10px;max-width:320px;line-height:1.4;
      animation:applyai-slide-in .3s ease`;
    toast.innerHTML = `
      <div style="font-size:10px;font-weight:700;color:${colors[type]};letter-spacing:1px;white-space:nowrap">ApplyAI</div>
      <div>${msg}</div>
      <div onclick="this.parentElement.remove()" style="cursor:pointer;color:#555;margin-left:auto;font-size:18px;line-height:1">×</div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast?.remove(), 6000);
  }
})();
