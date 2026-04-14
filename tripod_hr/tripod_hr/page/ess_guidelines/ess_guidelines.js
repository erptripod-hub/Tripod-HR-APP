frappe.pages['ess-guidelines'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'ESS Guidelines & Policies',
		single_column: true
	});

	// ── Styles ────────────────────────────────────────────────────────────
	$('<style id="ess-styles">').text(
		'#ess-wrap{padding:24px;background:#f0f2f5;min-height:100vh;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}' +
		'#ess-wrap *{box-sizing:border-box}' +
		'.ess-tabs{display:flex;gap:4px;background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:5px;margin-bottom:20px;width:fit-content}' +
		'.ess-tab{padding:8px 20px;font-size:13px;font-weight:500;border:none;border-radius:7px;cursor:pointer;transition:all .15s;background:transparent;color:#6b7280}' +
		'.ess-tab.active{background:#3b5bdb;color:#fff;font-weight:600}' +
		'.ess-panel{background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:14px}' +
		'.ess-panel-hd{padding:16px 20px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between}' +
		'.ess-panel-title{font-size:14px;font-weight:600;color:#1a1a2e;display:flex;align-items:center;gap:10px}' +
		'.ess-lock-badge{display:flex;align-items:center;gap:6px;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:5px 12px;font-size:11px;font-weight:600;color:#92400e}' +
		'.ess-file-row{display:flex;align-items:center;padding:14px 20px;border-bottom:1px solid #f9fafb;transition:background .1s}' +
		'.ess-file-row:last-child{border-bottom:none}' +
		'.ess-file-row:hover{background:#f9fafb}' +
		'.ess-file-ext{width:36px;height:40px;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#fff;margin-right:14px;flex-shrink:0}' +
		'.ess-file-name{font-size:13px;font-weight:600;color:#1a1a2e;margin-bottom:2px}' +
		'.ess-file-meta{font-size:11px;color:#9ca3af}' +
		'.ess-view-btn{padding:7px 18px;font-size:12px;font-weight:600;border:1px solid #bfdbfe;border-radius:7px;background:#eff6ff;color:#1d4ed8;cursor:pointer;transition:all .15s;margin-left:auto;flex-shrink:0;white-space:nowrap}' +
		'.ess-view-btn:hover{background:#dbeafe}' +
		'.ess-lock-note{padding:10px 20px;background:#fafbfc;border-top:1px solid #f3f4f6;font-size:11px;color:#9ca3af;display:flex;align-items:center;gap:6px}' +
		'.ess-viewer-hd{padding:14px 20px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between}' +
		'.ess-close-btn{padding:5px 14px;font-size:12px;border:1px solid #e5e7eb;border-radius:6px;background:#fff;color:#374151;cursor:pointer;font-weight:500}' +
		'.ess-close-btn:hover{background:#f9fafb}' +
		'.ess-table{width:100%;border-collapse:collapse;font-size:12px}' +
		'.ess-table th{background:#f8f9fc;padding:9px 14px;text-align:left;font-weight:600;color:#6b7280;border-bottom:2px solid #e5e7eb;white-space:nowrap}' +
		'.ess-table td{padding:9px 14px;border-bottom:1px solid #f3f4f6;color:#374151}' +
		'.ess-table tr:nth-child(even) td{background:#fafbfc}' +
		'.ess-table tr:hover td{background:#f5f7ff}' +
		'.ess-search-bar{display:flex;gap:10px;margin-bottom:16px}' +
		'.ess-search-input{flex:1;padding:9px 14px;font-size:13px;border:1px solid #e5e7eb;border-radius:8px;outline:none;color:#1a1a2e}' +
		'.ess-dept-select{padding:9px 14px;font-size:13px;border:1px solid #e5e7eb;border-radius:8px;outline:none;background:#fff;color:#374151}' +
		'.ess-dept-block{margin-bottom:14px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden}' +
		'.ess-dept-hd{padding:12px 20px;background:#f8f9fc;border-bottom:1px solid #f0f0f0;font-size:10.5px;font-weight:700;color:#9ca3af;letter-spacing:.7px;text-transform:uppercase}' +
		'.ess-policy-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:14px}' +
		'.ess-p-card{border:1px solid #e5e7eb;border-radius:9px;padding:13px 15px;cursor:pointer;transition:all .15s}' +
		'.ess-p-card:hover{border-color:#3b5bdb;background:#f5f7ff}' +
		'.ess-p-card-name{font-size:13px;font-weight:600;color:#1a1a2e;margin-bottom:5px}' +
		'.ess-p-card-meta{font-size:11px;color:#9ca3af;display:flex;align-items:center;gap:6px}' +
		'.ess-status{display:inline-flex;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px}' +
		'.ess-s-active{background:#f0fdf4;color:#166534}' +
		'.ess-s-review{background:#fffbeb;color:#92400e}' +
		'.ess-pol-section{margin-bottom:10px}' +
		'.ess-pol-title{font-size:13px;font-weight:700;color:#1a1a2e;margin:12px 0 4px;padding-bottom:5px;border-bottom:1px solid #f0f0f0}' +
		'.ess-pol-text{font-size:13px;color:#6b7280;line-height:1.7}'
	).appendTo('head');

	// ── Main container ────────────────────────────────────────────────────
	$(wrapper).find('.page-content').html(
		'<div id="ess-wrap">' +
		'<div class="ess-tabs">' +
		'<button class="ess-tab active" id="ess-tab-appt" onclick="essTab(\'appt\')">Appointment Guidelines</button>' +
		'<button class="ess-tab" id="ess-tab-policy" onclick="essTab(\'policy\')">Company Policies</button>' +
		'</div>' +
		'<div id="ess-section-appt"></div>' +
		'<div id="ess-section-policy" style="display:none">' +
		'<div class="ess-search-bar">' +
		'<input class="ess-search-input" id="ess-pol-search" type="text" placeholder="Search policies..." oninput="essFilterPolicies()">' +
		'<select class="ess-dept-select" id="ess-dept-filter" onchange="essFilterDept(this.value)"><option value="">All departments</option></select>' +
		'</div>' +
		'<div id="ess-policy-list"></div>' +
		'<div id="ess-pol-viewer" style="display:none"></div>' +
		'</div>' +
		'</div>'
	);

	// ── Tab switch ────────────────────────────────────────────────────────
	window.essTab = function(tab) {
		$('#ess-section-appt').toggle(tab === 'appt');
		$('#ess-section-policy').toggle(tab === 'policy');
		$('#ess-tab-appt').toggleClass('active', tab === 'appt');
		$('#ess-tab-policy').toggleClass('active', tab === 'policy');
	};

	// ── Load Appointment Guidelines ───────────────────────────────────────
	frappe.call({
		method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.get_guidelines',
		callback: function(r) {
			var data = (r && r.message && r.message.data) ? r.message.data : [];
			renderGuidelines(data);
		}
	});

	function renderGuidelines(data) {
		var html =
			'<div class="ess-panel">' +
			'<div class="ess-panel-hd">' +
			'<div class="ess-panel-title">Secure document folder</div>' +
			'<div class="ess-lock-badge">&#128274; Read-only &middot; No download</div>' +
			'</div>';

		if (!data || data.length === 0) {
			html += '<div style="padding:40px;text-align:center;color:#9ca3af;font-size:13px">No guidelines found. HR can add them via Appointment Guideline.</div>';
		} else {
			data.forEach(function(g) {
				var ext = g.guideline_file ? g.guideline_file.split('.').pop().toUpperCase() : 'FILE';
				var extBg = (ext === 'XLS' || ext === 'XLSX') ? '#1d6f42' : '#c0392b';
				var dept = g.department || 'General';
				var date = g.effective_date ? frappe.datetime.str_to_user(g.effective_date) : '';
				var statusBg = g.status === 'Active' ? 'background:#f0fdf4;color:#166534' : 'background:#f3f4f6;color:#374151';
				html +=
					'<div class="ess-file-row">' +
					'<div class="ess-file-ext" style="background:' + extBg + '">' + ext + '</div>' +
					'<div style="flex:1">' +
					'<div class="ess-file-name">' + frappe.utils.escape_html(g.title) + '</div>' +
					'<div class="ess-file-meta">' + frappe.utils.escape_html(dept) + (date ? ' &middot; ' + date : '') + '</div>' +
					'</div>' +
					'<span class="ess-status" style="' + statusBg + ';margin-right:12px">' + (g.status || '') + '</span>' +
					(g.guideline_file
						? '<button class="ess-view-btn" onclick="essViewFile(\'' + encodeURIComponent(g.guideline_file) + '\',\'' + frappe.utils.escape_html(g.title).replace(/'/g, "\\'") + '\')">View file</button>'
						: '<span style="font-size:11px;color:#d1d5db">No file attached</span>'
					) +
					'</div>';
			});
		}

		html +=
			'<div class="ess-lock-note">&#128274; In-browser view only. Right-click, print and save are disabled. Contact IT to change access.</div>' +
			'</div>' +
			'<div id="ess-file-viewer" style="display:none"></div>';

		$('#ess-section-appt').html(html);
	}

	// ── File viewer ───────────────────────────────────────────────────────
	window.essViewFile = function(encodedUrl, title) {
		var fileUrl = decodeURIComponent(encodedUrl);
		var ext = fileUrl.split('.').pop().toLowerCase();
		var fullUrl = window.location.origin + fileUrl;
		var viewerHtml;

		if (ext === 'pdf') {
			viewerHtml =
				'<div class="ess-panel" style="margin-top:14px">' +
				'<div class="ess-viewer-hd">' +
				'<div style="font-size:13px;font-weight:600;color:#1a1a2e">' + frappe.utils.escape_html(title) + '</div>' +
				'<div style="display:flex;align-items:center;gap:8px">' +
				'<span class="ess-lock-badge" style="font-size:10px">&#128274; View only</span>' +
				'<button class="ess-close-btn" onclick="$(\'#ess-file-viewer\').hide().html(\'\')">Close</button>' +
				'</div></div>' +
				'<div style="padding:16px;overflow-x:auto">' +
				'<div style="position:relative;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">' +
				'<div style="position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none"></div>' +
				'<iframe src="' + fullUrl + '#toolbar=0&navpanes=0" style="width:100%;height:600px;border:none" sandbox="allow-same-origin allow-scripts"></iframe>' +
				'</div></div></div>';
		} else {
			var officeUrl = 'https://view.officeapps.live.com/op/embed.aspx?src=' + encodeURIComponent(fullUrl);
			viewerHtml =
				'<div class="ess-panel" style="margin-top:14px">' +
				'<div class="ess-viewer-hd">' +
				'<div style="font-size:13px;font-weight:600;color:#1a1a2e">' + frappe.utils.escape_html(title) + '</div>' +
				'<div style="display:flex;align-items:center;gap:8px">' +
				'<span class="ess-lock-badge" style="font-size:10px">&#128274; View only</span>' +
				'<button class="ess-close-btn" onclick="$(\'#ess-file-viewer\').hide().html(\'\')">Close</button>' +
				'</div></div>' +
				'<div style="padding:16px;overflow-x:auto">' +
				'<div style="position:relative;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">' +
				'<div style="position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none"></div>' +
				'<iframe src="' + officeUrl + '" style="width:100%;height:500px;border:none"></iframe>' +
				'</div>' +
				'<div style="margin-top:8px;font-size:11px;color:#9ca3af;text-align:center">If the file does not load, the file may be private. Contact IT to enable preview.</div>' +
				'</div></div>';
		}

		$('#ess-file-viewer').html(viewerHtml).show();
		$('#ess-file-viewer')[0].scrollIntoView({behavior: 'smooth', block: 'nearest'});
	};

	// ── Load Company Policies ─────────────────────────────────────────────
	var allPoliciesData = {};

	frappe.call({
		method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.get_policies',
		callback: function(r) {
			if (r && r.message && r.message.success) {
				allPoliciesData = r.message.data || {};
				renderPolicies(allPoliciesData);
				// Populate dept filter
				Object.keys(allPoliciesData).sort().forEach(function(dept) {
					$('#ess-dept-filter').append('<option value="' + dept + '">' + dept + '</option>');
				});
			} else {
				$('#ess-policy-list').html('<div class="ess-panel" style="padding:40px;text-align:center;color:#9ca3af;font-size:13px">No policies found.</div>');
			}
		}
	});

	function renderPolicies(data) {
		var html = '';
		Object.keys(data).sort().forEach(function(dept) {
			var policies = data[dept];
			html += '<div class="ess-dept-block" data-dept="' + dept + '"><div class="ess-dept-hd">' + frappe.utils.escape_html(dept) + '</div><div class="ess-policy-grid">';
			policies.forEach(function(p) {
				var statusClass = p.status === 'Active' ? 'ess-s-active' : 'ess-s-review';
				var reviewed = p.last_reviewed ? frappe.datetime.str_to_user(p.last_reviewed) : '—';
				html +=
					'<div class="ess-p-card" onclick=\'essOpenPolicy(' + JSON.stringify(JSON.stringify(p)) + ')\'>' +
					'<div class="ess-p-card-name">' + frappe.utils.escape_html(p.policy_name) + '</div>' +
					'<div class="ess-p-card-meta"><span class="ess-status ' + statusClass + '">' + (p.status || '') + '</span> ' + reviewed + '</div>' +
					'</div>';
			});
			html += '</div></div>';
		});

		if (!html) html = '<div class="ess-panel" style="padding:40px;text-align:center;color:#9ca3af;font-size:13px">No policies found. HR can add them via Company Policy.</div>';
		$('#ess-policy-list').html(html);
	}

	window.essFilterPolicies = function() {
		var q = $('#ess-pol-search').val().toLowerCase();
		$('.ess-p-card').each(function() {
			var name = $(this).find('.ess-p-card-name').text().toLowerCase();
			$(this).toggle(!q || name.includes(q));
		});
	};

	window.essFilterDept = function(dept) {
		$('.ess-dept-block').each(function() {
			$(this).toggle(!dept || $(this).data('dept') === dept);
		});
	};

	window.essOpenPolicy = function(jsonStr) {
		var p = JSON.parse(jsonStr);
		var reviewed = p.last_reviewed ? frappe.datetime.str_to_user(p.last_reviewed) : '—';
		var html =
			'<div class="ess-panel" style="margin-top:14px">' +
			'<div class="ess-viewer-hd">' +
			'<div><div style="font-size:14px;font-weight:600;color:#1a1a2e">' + frappe.utils.escape_html(p.policy_name) + '</div>' +
			'<div style="font-size:11px;color:#9ca3af;margin-top:2px">' + (p.department || '') + (p.version ? ' &middot; v' + p.version : '') + '</div></div>' +
			'<div style="display:flex;gap:8px;align-items:center">' +
			'<span class="ess-lock-badge" style="font-size:10px">&#128274; View only</span>' +
			'<button class="ess-close-btn" onclick="$(\'#ess-pol-viewer\').hide().html(\'\')">Close</button>' +
			'</div></div>' +
			'<div style="padding:20px">' +
			'<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:7px;padding:8px 14px;margin-bottom:16px;font-size:12px;color:#92400e">&#128274; Policy document — view only. Last reviewed: ' + reviewed + '</div>' +
			(p.summary ? '<div class="ess-pol-section"><div class="ess-pol-title">Summary</div><div class="ess-pol-text">' + p.summary + '</div></div>' : '') +
			'<div class="ess-pol-section"><div class="ess-pol-title">1. Purpose</div><div class="ess-pol-text">This policy defines the rules and responsibilities for <strong>' + frappe.utils.escape_html(p.policy_name) + '</strong> across all Tripod MENA entities.</div></div>' +
			'<div class="ess-pol-section"><div class="ess-pol-title">2. Scope</div><div class="ess-pol-text">Applies to all full-time, part-time, and contracted employees' + (p.applicable_roles ? ' — roles: ' + p.applicable_roles : '') + '.</div></div>' +
			'<div class="ess-pol-section"><div class="ess-pol-title">3. Review Cycle</div><div class="ess-pol-text">Reviewed annually. Version: ' + (p.version || '1.0') + '</div></div>';

		if (p.policy_document) {
			var ext = p.policy_document.split('.').pop().toLowerCase();
			var fullUrl = window.location.origin + p.policy_document;
			var src = ext === 'pdf' ? fullUrl + '#toolbar=0&navpanes=0' : 'https://view.officeapps.live.com/op/embed.aspx?src=' + encodeURIComponent(fullUrl);
			html +=
				'<div class="ess-pol-section"><div class="ess-pol-title">Policy Document</div>' +
				'<div style="position:relative;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-top:8px">' +
				'<div style="position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none"></div>' +
				'<iframe src="' + src + '" style="width:100%;height:500px;border:none"></iframe></div></div>';
		}

		html += '</div></div>';
		$('#ess-pol-viewer').html(html).show();
		$('#ess-pol-viewer')[0].scrollIntoView({behavior: 'smooth', block: 'nearest'});
	};
};
