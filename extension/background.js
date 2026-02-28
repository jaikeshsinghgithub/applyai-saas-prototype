// ApplyAI Background Service Worker v2

chrome.runtime.onInstalled.addListener((details) => {
  console.log('[ApplyAI] Extension installed/updated', details.reason);

  // Set defaults on first install
  if (details.reason === 'install') {
    chrome.storage.local.set({
      applyai_settings: {
        auto_fill: true,
        portals: { naukri: true, linkedin: true, foundit: true, indeed: false }
      },
      applyai_stats: {
        today: 0, total: 0, linkedin: 0, naukri: 0, foundit: 0, lastReset: new Date().toDateString()
      }
    });
  }
});

// Reset daily stats at midnight
function checkDailyReset() {
  chrome.storage.local.get(['applyai_stats'], (data) => {
    const stats = data.applyai_stats || {};
    const today = new Date().toDateString();
    if (stats.lastReset !== today) {
      chrome.storage.local.set({
        applyai_stats: {
          ...stats,
          today: 0,
          lastReset: today
        }
      });
    }
  });
}

// Check every hour
checkDailyReset();
setInterval(checkDailyReset, 60 * 60 * 1000);

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  // Notification when form filled / applied
  if (msg.action === 'application_submitted') {
    chrome.notifications.create(`applyai_${Date.now()}`, {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: '✅ ApplyAI — Applied!',
      message: `Applied to ${msg.job_title} at ${msg.company}`
    });
  }

  // Update badge count
  if (msg.action === 'update_badge') {
    const count = msg.count || 0;
    chrome.action.setBadgeText({ text: count > 0 ? String(count) : '' });
    chrome.action.setBadgeBackgroundColor({ color: '#6366f1' });
  }

  // New application tracked from content script
  if (msg.action === 'track_application') {
    chrome.storage.local.get(['applyai_stats'], (data) => {
      const stats = data.applyai_stats || { today: 0, total: 0, linkedin: 0, naukri: 0, foundit: 0 };
      stats.today = (stats.today || 0) + 1;
      stats.total = (stats.total || 0) + 1;
      const portal = msg.portal || '';
      if (portal in stats) stats[portal]++;
      chrome.storage.local.set({ applyai_stats: stats });
      chrome.action.setBadgeText({ text: String(stats.today) });
      chrome.action.setBadgeBackgroundColor({ color: '#6366f1' });
    });
  }

  return true;
});
