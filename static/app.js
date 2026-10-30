// Tab Navigation
const tabs = document.querySelectorAll('.nav-tab');
const panes = document.querySelectorAll('.tab-pane');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    if (tab.tagName === 'A') return; // External link
    tabs.forEach(t => t.classList.remove('active'));
    panes.forEach(p => p.classList.remove('active'));

    tab.classList.add('active');
    const target = tab.dataset.tab;
    document.getElementById(target).classList.add('active');

    if (target === 'inboxTab') loadInbox();
    if (target === 'analyticsTab') loadAnalytics();
    if (target === 'spikesTab') loadIncidentSpikes();
  });
});

const pct = (n) => `${Math.round(Number(n) * 100)}%`;
let currentTicketId = null;

// Example Buttons
document.querySelectorAll('.example-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('ticket').value = btn.dataset.ticket;
    document.getElementById('custName').value = btn.dataset.name;
    document.getElementById('custTier').value = btn.dataset.tier;
  });
});

// Voice Speech-to-Text
const voiceBtn = document.getElementById('voiceBtn');
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    voiceBtn.classList.add('recording');
    voiceBtn.textContent = '🔴 Listening... (Speak now)';
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('ticket').value = transcript;
    voiceBtn.classList.remove('recording');
    voiceBtn.textContent = '🎙️ Speak / Voice Note';
  };

  recognition.onerror = () => {
    voiceBtn.classList.remove('recording');
    voiceBtn.textContent = '🎙️ Speak / Voice Note';
  };

  recognition.onend = () => {
    voiceBtn.classList.remove('recording');
    voiceBtn.textContent = '🎙️ Speak / Voice Note';
  };
}

voiceBtn?.addEventListener('click', () => {
  if (recognition) {
    try { recognition.start(); } catch (e) { recognition.stop(); }
  } else {
    // Simulated Voice Note if browser mic is not granted
    document.getElementById('ticket').value =
      "Hello, this is a voicemail from Sarah at FintechPro. We were charged twice this morning for our Pro plan. Please issue a refund for invoice #INV-8821 ASAP.";
    alert("Speech recognition simulated (Voice Note injected into ticket).");
  }
});

// Copy Reply
document.getElementById('copyReplyBtn')?.addEventListener('click', () => {
  const replyText = document.getElementById('resReply').value;
  navigator.clipboard.writeText(replyText);
  const btn = document.getElementById('copyReplyBtn');
  btn.textContent = '✅ Copied!';
  setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
});

// Single Ticket Triage
const analyzeBtn = document.getElementById('analyzeBtn');
const ticketInput = document.getElementById('ticket');
const statusMsg = document.getElementById('status');
const emptyState = document.getElementById('emptyTriageState');
const resultsWrapper = document.getElementById('results');

analyzeBtn.addEventListener('click', async () => {
  const val = ticketInput.value.trim();
  if (val.length < 5) {
    statusMsg.textContent = 'Please enter at least 5 characters.';
    return;
  }

  analyzeBtn.disabled = true;
  statusMsg.textContent = 'Running calibrated Jev triage, CRM 360 enrichment & tool planning...';

  try {
    const payload = {
      ticket: val,
      customer_name: document.getElementById('custName').value.trim() || 'Anonymous',
      customer_tier: document.getElementById('custTier').value,
      customer_email: `${document.getElementById('custName').value.trim().toLowerCase().replace(/\s+/g, '.')}@example.com`,
    };

    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Analysis request failed');

    currentTicketId = data.id;

    emptyState.classList.add('hidden');
    resultsWrapper.classList.remove('hidden');

    document.getElementById('resTicketId').textContent = `Ticket #${data.id}`;
    document.getElementById('resSlaBadge').textContent = `SLA: ${data.automation.sla_hours}h Deadline`;
    document.getElementById('resLangTag').textContent = `🌐 ${data.language}`;

    // CRM 360 Card
    if (data.customer) {
      document.getElementById('crmName').textContent = data.customer.name;
      document.getElementById('crmCompany').textContent = data.customer.company || 'Client Corp';
      document.getElementById('crmMrr').textContent = `$${data.customer.mrr || 0}`;
      document.getElementById('crmLtv').textContent = `$${data.customer.ltv || 0}`;
      document.getElementById('crmRenewal').textContent = `${data.customer.renewal_days_left}d`;
      document.getElementById('crmManager').textContent = data.customer.account_manager;

      const healthBadge = document.getElementById('crmHealthBadge');
      healthBadge.textContent = data.customer.health_status;
      healthBadge.className = 'health-badge';
      if (data.customer.health_status.includes('Critical') || data.customer.health_status.includes('Risk')) {
        healthBadge.classList.add('critical');
      }
    }

    // Sentiment badge
    const sentBadge = document.getElementById('resSentimentBadge');
    sentBadge.textContent = data.sentiment.mood;
    sentBadge.className = 'sentiment-badge';
    if (data.sentiment.mood.includes('Angry')) sentBadge.classList.add('angry');
    else if (data.sentiment.mood.includes('Frustrated')) sentBadge.classList.add('frustrated');

    // Retention Playbook Banner
    const retBanner = document.getElementById('resRetentionBanner');
    if (data.sentiment.retention_playbook) {
      document.getElementById('resRetentionText').textContent = data.sentiment.retention_playbook;
      retBanner.classList.remove('hidden');
    } else {
      retBanner.classList.add('hidden');
    }

    // Webhook alert indicator
    const webhookAlert = document.getElementById('resWebhookAlert');
    if (data.automation.webhook_alert) {
      webhookAlert.classList.remove('hidden');
    } else {
      webhookAlert.classList.add('hidden');
    }

    // Reset tool receipt
    const receiptBox = document.getElementById('toolExecutionReceipt');
    receiptBox.classList.add('hidden');
    receiptBox.innerHTML = '';

    // Decision metrics
    document.getElementById('resDept').textContent = data.jev.department;
    document.getElementById('resDeptConf').textContent = `${pct(data.jev.department_confidence)} confidence`;
    document.getElementById('resUrgency').textContent = Number(data.jev.urgency_score).toFixed(2);
    document.getElementById('resRefund').textContent = pct(data.jev.refund_probability);
    document.getElementById('resHuman').textContent = pct(data.jev.human_review_probability);

    document.getElementById('resRoute').textContent = data.automation.route;
    document.getElementById('resReason').textContent = data.automation.reason;

    const pill = document.getElementById('resEscalationPill');
    if (data.automation.needs_human) {
      pill.textContent = '⚠️ Escalated';
      pill.className = 'pill-badge escalated';
    } else {
      pill.textContent = '✅ Safe Queue';
      pill.className = 'pill-badge';
    }

    // Knowledge base badges
    const kbContainer = document.getElementById('resKbContainer');
    kbContainer.innerHTML = '';
    if (data.knowledge_sources && data.knowledge_sources.length > 0) {
      data.knowledge_sources.forEach(src => {
        const tag = document.createElement('span');
        tag.className = 'kb-tag';
        tag.textContent = `📖 ${src.title}`;
        tag.title = src.excerpt;
        kbContainer.appendChild(tag);
      });
    }

    // Suggested reply
    document.getElementById('resReply').value = data.suggested_reply;

    statusMsg.textContent = data.jev.is_simulated
      ? 'Evaluated via simulated Jev fallback (configure TYPESAFE_API_KEY for live API).'
      : 'Evaluated with live TypeSafe Jev API.';

    updateInboxCount();
  } catch (err) {
    statusMsg.textContent = `Error: ${err.message}`;
  } finally {
    analyzeBtn.disabled = false;
  }
});

// Tool Calling Action Simulator Handlers
async function executeTool(actionType, extraData = {}) {
  if (!currentTicketId) return;
  const receiptBox = document.getElementById('toolExecutionReceipt');
  receiptBox.classList.remove('hidden');
  receiptBox.innerHTML = `<em>Executing tool: ${actionType}...</em>`;

  try {
    const res = await fetch(`/api/tickets/${currentTicketId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_type: actionType, ...extraData }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Tool execution failed');

    receiptBox.innerHTML = `
      <strong>⚡ Action Executed (${data.action_id}):</strong><br/>
      ${data.message}<br/>
      <small style="color:#d1fae5;">Timestamp: ${data.executed_at}</small>
    `;
    statusMsg.textContent = `Tool ${actionType} logged to ticket audit trail!`;
  } catch (err) {
    receiptBox.innerHTML = `<span style="color:#fecaca;">Failed: ${err.message}</span>`;
  }
}

document.getElementById('stripeRefundBtn')?.addEventListener('click', () => {
  executeTool('stripe_refund', { amount: 29.0, reason: 'duplicate_charge_triage' });
});

document.getElementById('auth0ResetBtn')?.addEventListener('click', () => {
  executeTool('auth0_reset');
});

document.getElementById('sessionUnlockBtn')?.addEventListener('click', () => {
  executeTool('session_unlock');
});

// Branded Email Dispatcher Modal
const emailModal = document.getElementById('emailModal');
const closeEmailModalBtn = document.getElementById('closeEmailModalBtn');
const emailPreviewFrame = document.getElementById('emailPreviewFrame');
const emailPreviewBtn = document.getElementById('emailPreviewBtn');
const confirmSendEmailBtn = document.getElementById('confirmSendEmailBtn');

closeEmailModalBtn?.addEventListener('click', () => emailModal.classList.add('hidden'));

emailPreviewBtn?.addEventListener('click', async () => {
  if (!currentTicketId) return;
  emailModal.classList.remove('hidden');
  emailPreviewFrame.innerHTML = '<div class="text-muted">Generating branded HTML preview...</div>';

  try {
    const replyText = document.getElementById('resReply').value;
    const res = await fetch(`/api/tickets/${currentTicketId}/send-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body: replyText })
    });
    const data = await res.json();
    emailPreviewFrame.innerHTML = data.html;
  } catch (e) {
    emailPreviewFrame.innerHTML = `<div class="text-danger">Failed to generate preview: ${e.message}</div>`;
  }
});

confirmSendEmailBtn?.addEventListener('click', () => {
  alert(`Resolution email dispatched to customer for Ticket #${currentTicketId}!`);
  emailModal.classList.add('hidden');
});

// Human Actions
document.getElementById('approveBtn').addEventListener('click', async () => {
  if (!currentTicketId) return;
  const reply = document.getElementById('resReply').value;
  await fetch(`/api/tickets/${currentTicketId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'resolved', final_reply: reply }),
  });
  statusMsg.textContent = `Ticket #${currentTicketId} marked as Resolved!`;
  updateInboxCount();
});

document.getElementById('escalateBtn').addEventListener('click', async () => {
  if (!currentTicketId) return;
  await fetch(`/api/tickets/${currentTicketId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'escalated' }),
  });
  statusMsg.textContent = `Ticket #${currentTicketId} escalated to senior specialist rotation.`;
  updateInboxCount();
});

document.getElementById('overrideDeptSelect').addEventListener('change', async (e) => {
  if (!currentTicketId || !e.target.value) return;
  const newDept = e.target.value;
  await fetch(`/api/tickets/${currentTicketId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ override_department: newDept }),
  });
  document.getElementById('resDept').textContent = newDept;
  statusMsg.textContent = `Department overridden to ${newDept} by human agent.`;
  e.target.value = '';
  updateInboxCount();
});

// Incident Spikes & Jira Auto-Generator
async function loadIncidentSpikes() {
  const container = document.getElementById('spikesContainer');
  container.innerHTML = '<div class="card text-center" style="grid-column: 1 / -1; padding: 40px;"><p class="text-muted">Clustering tickets & detecting engineering regressions...</p></div>';

  try {
    const res = await fetch('/api/engineering-spikes');
    const data = await res.json();

    if (!data.active_clusters.length) {
      container.innerHTML = '<div class="card text-center" style="grid-column: 1 / -1; padding: 40px;"><p class="text-muted">No active incident spikes detected. Systems normal.</p></div>';
      return;
    }

    container.innerHTML = data.active_clusters.map(c => `
      <div class="spike-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span class="pill-badge ${c.severity.includes('P1') ? 'escalated' : ''}">${c.severity}</span>
          <small class="text-muted">${c.affected_tickets_count} Linked Tickets</small>
        </div>
        <h3>${c.topic}</h3>
        <p style="font-size: 13px; color: #cbd5e1; margin-bottom: 8px;">
          <strong>Pattern:</strong> ${c.detected_pattern}
        </p>
        <div class="jira-box">${c.jira_issue.body}</div>
        <button class="btn btn-secondary" style="margin-top: 12px; font-size: 12px; padding: 6px 12px;" onclick="copyJiraText(\`${encodeURIComponent(c.jira_issue.body)}\`)">
          📋 Copy Jira / GitHub Issue Markdown
        </button>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="card text-center text-danger" style="grid-column: 1 / -1; padding: 40px;">Error: ${err.message}</div>`;
  }
}

document.getElementById('refreshSpikesBtn')?.addEventListener('click', loadIncidentSpikes);

window.copyJiraText = (encoded) => {
  navigator.clipboard.writeText(decodeURIComponent(encoded));
  alert('Jira issue markdown copied to clipboard!');
};

// Inbox Queue
async function loadInbox(filter = 'all') {
  const tbody = document.getElementById('inboxTableBody');
  tbody.innerHTML = '<tr><td colspan="9" class="text-center">Loading ticket queue...</td></tr>';

  try {
    const res = await fetch(`/api/tickets?status=${filter}`);
    const tickets = await res.json();

    if (tickets.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No tickets found in this queue.</td></tr>';
      return;
    }

    tbody.innerHTML = tickets.map(t => `
      <tr>
        <td><strong>#${t.id}</strong></td>
        <td>${t.customer_name} <span class="sla-badge" style="font-size:10px;">${t.customer_tier}</span></td>
        <td>${t.language || 'English'}</td>
        <td><span class="sentiment-badge ${String(t.sentiment || '').includes('Angry') ? 'angry' : ''}">${t.sentiment || 'Calm'}</span></td>
        <td style="text-transform: capitalize;">${t.department}</td>
        <td>${Number(t.urgency_score).toFixed(2)}</td>
        <td>${t.sla_deadline_hours}h</td>
        <td><span class="status-badge status-${t.status}">${t.status}</span></td>
        <td>
          <button class="btn btn-secondary" style="padding:4px 8px;font-size:11px;" onclick="openThreadModal(${t.id})">💬 Thread</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Failed to load: ${err.message}</td></tr>`;
  }
}

// Conversation Thread Modal
let activeThreadTicketId = null;
const threadModal = document.getElementById('threadModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const modalContainer = document.getElementById('modalMessagesContainer');
const followupInput = document.getElementById('followupInput');
const sendFollowupBtn = document.getElementById('sendFollowupBtn');

closeModalBtn?.addEventListener('click', () => threadModal.classList.add('hidden'));

async function openThreadModal(ticketId) {
  activeThreadTicketId = ticketId;
  document.getElementById('modalThreadTitle').textContent = `Ticket #${ticketId} Conversation Thread`;
  threadModal.classList.remove('hidden');
  modalContainer.innerHTML = '<div class="text-muted">Loading messages...</div>';

  try {
    const res = await fetch(`/api/tickets/${ticketId}/messages`);
    const messages = await res.json();

    if (!messages.length) {
      modalContainer.innerHTML = '<div class="text-muted">No messages found.</div>';
      return;
    }

    modalContainer.innerHTML = messages.map(m => `
      <div class="message-bubble ${m.sender}">
        <strong>${m.sender.toUpperCase()}:</strong><br/>
        ${m.message_text}
      </div>
    `).join('');
  } catch (err) {
    modalContainer.innerHTML = `<div class="text-danger">Error: ${err.message}</div>`;
  }
}

sendFollowupBtn?.addEventListener('click', async () => {
  const text = followupInput.value.trim();
  if (!text || !activeThreadTicketId) return;

  await fetch(`/api/tickets/${activeThreadTicketId}/reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sender: 'agent', message: text }),
  });

  followupInput.value = '';
  openThreadModal(activeThreadTicketId);
});

// Batch Processing
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('csvFileInput');
const uploadBtn = document.getElementById('uploadCsvBtn');
const batchStatus = document.getElementById('batchStatus');

dropZone?.addEventListener('click', () => fileInput.click());

fileInput?.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    dropZone.querySelector('p').textContent = `Selected: ${fileInput.files[0].name}`;
    uploadBtn.disabled = false;
  }
});

uploadBtn?.addEventListener('click', async () => {
  if (!fileInput.files.length) return;
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  batchStatus.textContent = 'Uploading and evaluating CSV tickets concurrently...';
  uploadBtn.disabled = true;

  try {
    const res = await fetch('/api/upload-csv', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');

    renderBatchSummary(data);
    batchStatus.textContent = `Successfully processed ${data.processed} tickets!`;
    updateInboxCount();
  } catch (err) {
    batchStatus.textContent = 'Error: ' + err.message;
  } finally {
    uploadBtn.disabled = false;
  }
});

document.getElementById('loadDemoBatchBtn')?.addEventListener('click', async () => {
  batchStatus.textContent = 'Running demo batch triage (3 diverse tickets)...';
  try {
    const res = await fetch('/api/batch-analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: [
          { ticket: "I was charged twice for my Pro subscription this morning. I need duplicate charge refunded.", customer_name: "Sarah Jenkins", customer_tier: "Pro" },
          { ticket: "My CSV export stopped working after today's update. Dashboard works fine.", customer_name: "Marcus Vance", customer_tier: "Free" },
          { ticket: "I cannot access the workspace after my admin changed my email address.", customer_name: "Elena Rostova", customer_tier: "Enterprise" },
        ]
      }),
    });
    const data = await res.json();
    renderBatchSummary(data);
    batchStatus.textContent = `Completed demo batch (${data.processed} tickets processed and saved).`;
    updateInboxCount();
  } catch (err) {
    batchStatus.textContent = 'Batch error: ' + err.message;
  }
});

function renderBatchSummary(data) {
  const summaryDiv = document.getElementById('batchSummary');
  summaryDiv.innerHTML = `
    <div style="margin-bottom:12px;font-size:13px;color:#a5b4fc;">
      Total Processed: <strong>${data.processed}</strong> tickets
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Customer</th>
          <th>Sentiment</th>
          <th>Department</th>
          <th>Urgency</th>
          <th>SLA</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${data.tickets.map(t => `
          <tr>
            <td>#${t.id}</td>
            <td>${t.name} (${t.tier})</td>
            <td>${t.sentiment || 'Calm'}</td>
            <td style="text-transform: capitalize;">${t.department}</td>
            <td>${Number(t.urgency).toFixed(2)}</td>
            <td>${t.sla_hours}h</td>
            <td><span class="status-badge ${t.needs_human ? 'status-escalated' : 'status-triaged'}">${t.needs_human ? 'Escalated' : 'Queued'}</span></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// Analytics Charts
let deptChartInstance = null;
let urgencyChartInstance = null;
let tierChartInstance = null;

async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();

    document.getElementById('kpiTotal').textContent = data.total_tickets;
    document.getElementById('kpiEscalation').textContent = `${data.escalation_rate}%`;
    document.getElementById('kpiUrgency').textContent = data.avg_urgency;
    document.getElementById('kpiConfidence').textContent = `${data.avg_department_confidence}%`;

    const deptCtx = document.getElementById('deptChart').getContext('2d');
    if (deptChartInstance) deptChartInstance.destroy();
    deptChartInstance = new Chart(deptCtx, {
      type: 'doughnut',
      data: {
        labels: ['Billing', 'Technical', 'Account', 'General'],
        datasets: [{
          data: [
            data.department_counts.billing,
            data.department_counts.technical,
            data.department_counts.account,
            data.department_counts.general,
          ],
          backgroundColor: ['#6366f1', '#06b6d4', '#f59e0b', '#64748b'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } } },
      },
    });

    const urgCtx = document.getElementById('urgencyChart').getContext('2d');
    if (urgencyChartInstance) urgencyChartInstance.destroy();
    urgencyChartInstance = new Chart(urgCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(data.urgency_buckets),
        datasets: [{
          label: 'Tickets',
          data: Object.values(data.urgency_buckets),
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          borderRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
          y: { ticks: { color: '#94a3b8', stepSize: 1 }, grid: { color: '#334155' } },
        },
      },
    });

    const tierCtx = document.getElementById('tierChart').getContext('2d');
    if (tierChartInstance) tierChartInstance.destroy();
    tierChartInstance = new Chart(tierCtx, {
      type: 'pie',
      data: {
        labels: Object.keys(data.tier_counts),
        datasets: [{
          data: Object.values(data.tier_counts),
          backgroundColor: ['#64748b', '#6366f1', '#ec4899'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } } },
      },
    });
  } catch (err) {
    console.error('Failed to load analytics', err);
  }
}

document.getElementById('refreshAnalyticsBtn')?.addEventListener('click', loadAnalytics);

async function updateInboxCount() {
  try {
    const res = await fetch('/api/tickets?status=all');
    const list = await res.json();
    document.getElementById('inboxCount').textContent = list.length;
  } catch (e) {}
}

window.openThreadModal = openThreadModal;
updateInboxCount();
