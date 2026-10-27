frappe.pages['ess-guidelines'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Appointment Guidelines',
		single_column: true
	});

	if (!document.getElementById('ess-gl-styles')) {
		$('<style id="ess-gl-styles">').text(
			'.ess-gl-wrap{max-width:960px;margin:24px auto;padding:0 20px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}' +
			'.ess-gl-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}' +
			'.ess-gl-title{font-size:20px;font-weight:700;color:#1a1a2e}' +
			'.ess-gl-subtitle{font-size:12px;color:#9ca3af;margin-top:3px}' +
			'.ess-gl-badge{display:flex;align-items:center;gap:8px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 14px}' +
			'.ess-gl-badge-name{font-size:12px;font-weight:600;color:#1a1a2e}' +
			'.ess-gl-badge-co{font-size:10px;color:#9ca3af}' +
			'.ess-gl-card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:16px}' +
			'.ess-gl-card-hd{padding:14px 20px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}' +
			'.ess-gl-card-title{font-size:14px;font-weight:600;color:#1a1a2e;display:flex;align-items:center;gap:8px}' +
			'.ess-gl-lock{display:flex;align-items:center;gap:5px;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;color:#92400e}' +
			'.ess-gl-pdf-wrap{position:relative}' +
			'.ess-gl-pdf-overlay{position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none}' +
			'.ess-gl-pdf-frame{width:100%;height:700px;border:none;display:block}' +
			'.ess-gl-ack-bar{padding:16px 20px;border-top:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}' +
			'.ess-gl-ack-btn{padding:10px 28px;font-size:13px;font-weight:700;border:none;border-radius:8px;cursor:pointer;background:#3b5bdb;color:#fff;transition:all .15s}' +
			'.ess-gl-ack-btn:hover{background:#2f4ac0}' +
			'.ess-gl-ack-btn:disabled{background:#9ca3af;cursor:not-allowed}' +
			'.ess-gl-ack-done{display:flex;align-items:center;gap:6px;font-size:13px;font-weight:600;color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:8px 16px}' +
			'.ess-gl-footer{padding:10px 20px;background:#fafbfc;border-top:1px solid #f3f4f6;font-size:11px;color:#9ca3af}' +
			'.ess-gl-empty{padding:60px 20px;text-align:center;color:#9ca3af;font-size:14px}' +
			'.ess-gl-error{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px 20px;color:#991b1b;font-size:13px}' +
			'.ess-gl-tabs{display:flex;gap:4px;margin-bottom:16px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:4px;width:fit-content}' +
			'.ess-gl-tab{padding:7px 18px;font-size:12px;font-weight:500;border:none;border-radius:6px;cursor:pointer;background:transparent;color:#6b7280;transition:all .15s}' +
			'.ess-gl-tab.active{background:#3b5bdb;color:#fff;font-weight:600}' +
			'.ess-rpt-bar{display:flex;gap:12px;margin-bottom:16px}' +
			'.ess-rpt-stat{flex:1;background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;text-align:center}' +
			'.ess-rpt-num{font-size:28px;font-weight:700;color:#1a1a2e}' +
			'.ess-rpt-lbl{font-size:11px;color:#9ca3af;margin-top:2px}' +
			'.ess-rpt-table{width:100%;border-collapse:collapse;font-size:13px}' +
			'.ess-rpt-table th{padding:10px 14px;text-align:left;font-weight:600;color:#6b7280;border-bottom:2px solid #e5e7eb;background:#f8f9fc}' +
			'.ess-rpt-table td{padding:10px 14px;border-bottom:1px solid #f3f4f6;color:#374151}' +
			'.ess-rpt-table tr:hover td{background:#f9fafb}' +
			'.ess-pill-green{background:#f0fdf4;color:#166534;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;display:inline-block}' +
			'.ess-pill-red{background:#fef2f2;color:#991b1b;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;display:inline-block}'
		).appendTo('head');
	}

	var $body = $(wrapper).find('.page-content');
	$body.html('<div class="ess-gl-wrap"><div style="padding:60px;text-align:center;color:#9ca3af">Loading...</div></div>');
	var $wrap = $body.find('.ess-gl-wrap');

	var isHR = frappe.user.has_role(['HR Manager','HR User','System Manager']);

	frappe.call({
		method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.get_my_guideline',
		callback: function(r) {
			if (!r || !r.message) { showError($wrap,'Could not load. Please refresh.'); return; }
			var d = r.message;
			if (!d.success) { showError($wrap, d.error); return; }
			if (d.is_admin) { renderAdmin($wrap, d); } else { renderEmployee($wrap, d); }
		},
		error: function(){ showError($wrap,'Server error. Please refresh.'); }
	});

	// ── Employee view ─────────────────────────────────────────────────────
	function renderEmployee($wrap, d) {
		var emp = d.employee, g = d.guideline;
		var html = makeHeader(emp);
		if (!g || !g.guideline_file) {
			html += '<div class="ess-gl-card"><div class="ess-gl-empty">📋 No guidelines uploaded for <strong>' +
				frappe.utils.escape_html(emp.company) + '</strong> yet. Please contact HR.</div></div>';
			$wrap.html(html); return;
		}
		html += makeFileCard(g, emp.company, d.acknowledged, emp.id, g.name);
		$wrap.html(html);
		bindAck($wrap, emp.id, g.name);
		$wrap[0].addEventListener('contextmenu', function(e){ e.preventDefault(); });
	}

	// ── Admin view ────────────────────────────────────────────────────────
	function renderAdmin($wrap, d) {
		var guidelines = d.guidelines || [];
		var html = '<div class="ess-gl-header"><div><div class="ess-gl-title">Appointment Guidelines</div>' +
			'<div class="ess-gl-subtitle">Admin view — all companies</div></div>' +
			'<div class="ess-gl-badge"><div style="width:32px;height:32px;border-radius:50%;background:#3b5bdb;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff">AD</div>' +
			'<div><div class="ess-gl-badge-name">Administrator</div><div class="ess-gl-badge-co">All Companies</div></div></div></div>';

		if (!guidelines.length) {
			html += '<div class="ess-gl-card"><div class="ess-gl-empty">📋 No active guidelines found.</div></div>';
			$wrap.html(html); return;
		}

		if (guidelines.length > 1) {
			html += '<div class="ess-gl-tabs">';
			guidelines.forEach(function(g, i) {
				html += '<button class="ess-gl-tab' + (i===0?' active':'') + '" onclick="essTab('+i+')">' + frappe.utils.escape_html(g.company) + '</button>';
			});
			html += '</div>';
		}

		guidelines.forEach(function(g, i) {
			html += '<div class="ess-gl-admin-panel" id="ess-panel-'+i+'" style="'+(i===0?'':'display:none')+'">';
			html += makeFileCard(g, g.company, false, null, g.name, true);
			html += '</div>';
		});

		$wrap.html(html);
		$wrap[0].addEventListener('contextmenu', function(e){ e.preventDefault(); });

		// Load report for first guideline
		if (guidelines[0]) loadReport($wrap, guidelines[0].name, 0);

		window.essTab = function(idx) {
			$('.ess-gl-admin-panel').hide();
			$('#ess-panel-'+idx).show();
			$('.ess-gl-tab').removeClass('active').eq(idx).addClass('active');
			if (guidelines[idx]) loadReport($wrap, guidelines[idx].name, idx);
		};
	}

	// ── Acknowledgement button binding ────────────────────────────────────
	function bindAck($wrap, empId, guidelineName) {
		$wrap.find('#ess-ack-btn').on('click', function() {
			var $btn = $(this);
			$btn.prop('disabled', true).text('Submitting...');
			frappe.call({
				method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.acknowledge',
				args: {employee: empId, guideline: guidelineName},
				callback: function(r) {
					if (r && r.message) {
						$wrap.find('#ess-ack-area').html(
							'<div class="ess-gl-ack-done">✅ Acknowledged — ' +
							frappe.datetime.str_to_user(r.message.acknowledged_on || frappe.datetime.now_datetime()) +
							'</div>'
						);
					}
				},
				error: function(){ $btn.prop('disabled',false).text('I Acknowledge'); }
			});
		});
	}

	// ── HR acknowledgement report ─────────────────────────────────────────
	function loadReport($wrap, guidelineName, panelIdx) {
		var $panel = $wrap.find('#ess-panel-'+panelIdx+' .ess-rpt-section');
		if (!$panel.length) return;
		$panel.html('<div style="padding:20px;text-align:center;color:#9ca3af;font-size:12px">Loading report...</div>');

		frappe.call({
			method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.get_acknowledgement_report',
			args: {guideline: guidelineName},
			callback: function(r) {
				if (!r || !r.message) return;
				var d = r.message;
				var pct = d.total ? Math.round((d.ack_count/d.total)*100) : 0;
				var html =
					'<div class="ess-rpt-bar">' +
					stat(d.total, 'Total Employees') +
					stat(d.ack_count, 'Acknowledged', '#166534') +
					stat(d.pending_count, 'Pending', '#991b1b') +
					stat(pct+'%', 'Completion') +
					'</div>';

				// Pending table
				if (d.pending.length) {
					html += '<div style="font-size:12px;font-weight:600;color:#991b1b;margin-bottom:8px">⏳ Pending ('+d.pending.length+')</div>';
					html += '<div class="ess-gl-card" style="margin-bottom:14px"><table class="ess-rpt-table"><thead><tr><th>Employee</th><th>Designation</th><th>Department</th><th>Status</th></tr></thead><tbody>';
					d.pending.forEach(function(e) {
						html += '<tr><td>'+frappe.utils.escape_html(e.employee_name)+'</td><td>'+frappe.utils.escape_html(e.designation||'—')+'</td><td>'+frappe.utils.escape_html(e.department||'—')+'</td><td><span class="ess-pill-red">Pending</span></td></tr>';
					});
					html += '</tbody></table></div>';
				}

				// Acknowledged table
				if (d.acknowledged.length) {
					html += '<div style="font-size:12px;font-weight:600;color:#166534;margin-bottom:8px">✅ Acknowledged ('+d.acknowledged.length+')</div>';
					html += '<div class="ess-gl-card"><table class="ess-rpt-table"><thead><tr><th>Employee</th><th>Designation</th><th>Department</th><th>Acknowledged On</th></tr></thead><tbody>';
					d.acknowledged.forEach(function(e) {
						html += '<tr><td>'+frappe.utils.escape_html(e.employee_name)+'</td><td>'+frappe.utils.escape_html(e.designation||'—')+'</td><td>'+frappe.utils.escape_html(e.department||'—')+'</td><td><span class="ess-pill-green">'+frappe.datetime.str_to_user(e.acknowledged_on)+'</span></td></tr>';
					});
					html += '</tbody></table></div>';
				}

				$panel.html(html);
			}
		});
	}

	function stat(val, lbl, color) {
		return '<div class="ess-rpt-stat"><div class="ess-rpt-num"'+(color?' style="color:'+color+'"':'')+'>'+val+'</div><div class="ess-rpt-lbl">'+lbl+'</div></div>';
	}

	// ── Helpers ───────────────────────────────────────────────────────────
	function makeFileCard(g, company, acknowledged, empId, guidelineName, adminMode) {
		var fileUrl = g.guideline_file;
		var ext = fileUrl.split('.').pop().toLowerCase();
		var date = g.effective_date ? frappe.datetime.str_to_user(g.effective_date) : '';
		var fullUrl = window.location.origin + fileUrl;
		var src = ext === 'pdf'
			? fullUrl + '#toolbar=0&navpanes=0&scrollbar=1'
			: 'https://view.officeapps.live.com/op/embed.aspx?src=' + encodeURIComponent(fullUrl);

		var ackHtml = '';
		if (!adminMode) {
			if (acknowledged) {
				ackHtml = '<div class="ess-gl-ack-bar"><div id="ess-ack-area"><div class="ess-gl-ack-done">✅ You have acknowledged this guideline</div></div></div>';
			} else {
				ackHtml = '<div class="ess-gl-ack-bar">' +
					'<div style="font-size:12px;color:#6b7280">Please read the guideline above, then click to confirm you have read and understood it.</div>' +
					'<div id="ess-ack-area"><button class="ess-gl-ack-btn" id="ess-ack-btn">✔ I Acknowledge</button></div>' +
					'</div>';
			}
		}

		var rptSection = adminMode ? '<div class="ess-rpt-section" style="padding:16px 20px;border-top:1px solid #f3f4f6"></div>' : '';

		return '<div class="ess-gl-card">' +
			'<div class="ess-gl-card-hd">' +
			'<div class="ess-gl-card-title">📁 ' + frappe.utils.escape_html(g.title) +
			'<span style="font-size:11px;color:#9ca3af;font-weight:400">' + frappe.utils.escape_html(company) + (date?' · '+date:'') + '</span></div>' +
			'<div class="ess-gl-lock">🔒 View only — no download</div>' +
			'</div>' +
			'<div class="ess-gl-pdf-wrap"><div class="ess-gl-pdf-overlay"></div>' +
			'<iframe class="ess-gl-pdf-frame" src="' + src + '" sandbox="allow-same-origin allow-scripts allow-forms"></iframe>' +
			'</div>' +
			ackHtml +
			'<div class="ess-gl-footer">🔒 Secured view — right-click, print and save are disabled.</div>' +
			rptSection +
			'</div>';
	}

	function makeHeader(emp) {
		var initials = (emp.name||'U').split(' ').map(function(n){return n[0];}).join('').substring(0,2).toUpperCase();
		return '<div class="ess-gl-header">' +
			'<div><div class="ess-gl-title">Appointment Guidelines</div>' +
			'<div class="ess-gl-subtitle">Secure read-only document — downloading is disabled.</div></div>' +
			'<div class="ess-gl-badge"><div style="width:32px;height:32px;border-radius:50%;background:#3b5bdb;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff">'+initials+'</div>' +
			'<div><div class="ess-gl-badge-name">'+frappe.utils.escape_html(emp.name)+'</div>' +
			'<div class="ess-gl-badge-co">'+frappe.utils.escape_html(emp.company)+'</div></div></div></div>';
	}

	function showError($wrap, msg) {
		$wrap.html('<div class="ess-gl-header"><div class="ess-gl-title">Appointment Guidelines</div></div>' +
			'<div class="ess-gl-error">⚠️ '+frappe.utils.escape_html(msg)+'</div>');
	}
};
