frappe.pages['ess-guidelines'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Appointment Guidelines',
		single_column: true
	});

	if (!document.getElementById('ess-gl-styles')) {
		$('<style id="ess-gl-styles">').text(
			'.ess-gl-wrap{max-width:900px;margin:24px auto;padding:0 20px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}' +
			'.ess-gl-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}' +
			'.ess-gl-title{font-size:20px;font-weight:700;color:#1a1a2e}' +
			'.ess-gl-subtitle{font-size:12px;color:#9ca3af;margin-top:3px}' +
			'.ess-gl-badge{display:flex;align-items:center;gap:8px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 14px}' +
			'.ess-gl-badge-name{font-size:12px;font-weight:600;color:#1a1a2e}' +
			'.ess-gl-badge-co{font-size:10px;color:#9ca3af}' +
			'.ess-gl-card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:16px}' +
			'.ess-gl-card-hd{padding:14px 20px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between}' +
			'.ess-gl-card-title{font-size:14px;font-weight:600;color:#1a1a2e;display:flex;align-items:center;gap:8px}' +
			'.ess-gl-lock{display:flex;align-items:center;gap:5px;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;color:#92400e}' +
			'.ess-gl-pdf-wrap{position:relative}' +
			'.ess-gl-pdf-overlay{position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none}' +
			'.ess-gl-pdf-frame{width:100%;height:700px;border:none;display:block}' +
			'.ess-gl-footer{padding:10px 20px;background:#fafbfc;border-top:1px solid #f3f4f6;font-size:11px;color:#9ca3af;display:flex;align-items:center;gap:5px}' +
			'.ess-gl-empty{padding:60px 20px;text-align:center;color:#9ca3af;font-size:14px}' +
			'.ess-gl-error{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px 20px;color:#991b1b;font-size:13px}' +
			'.ess-gl-tabs{display:flex;gap:4px;margin-bottom:16px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:4px;width:fit-content}' +
			'.ess-gl-tab{padding:7px 18px;font-size:12px;font-weight:500;border:none;border-radius:6px;cursor:pointer;background:transparent;color:#6b7280;transition:all .15s}' +
			'.ess-gl-tab.active{background:#3b5bdb;color:#fff;font-weight:600}'
		).appendTo('head');
	}

	var $body = $(wrapper).find('.page-content');
	$body.html('<div class="ess-gl-wrap"><div style="padding:60px;text-align:center;color:#9ca3af">Loading...</div></div>');
	var $wrap = $body.find('.ess-gl-wrap');

	frappe.call({
		method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.get_my_guideline',
		callback: function(r) {
			if (!r || !r.message) { showError($wrap, 'Could not load. Please refresh.'); return; }
			var d = r.message;
			if (!d.success) { showError($wrap, d.error); return; }
			if (d.is_admin) { renderAdmin($wrap, d); } else { renderEmployee($wrap, d); }
		},
		error: function() { showError($wrap, 'Server error. Please refresh.'); }
	});

	function renderEmployee($wrap, d) {
		var emp = d.employee;
		var g = d.guideline;
		var html = makeHeader(emp);
		if (!g || !g.guideline_file) {
			html += '<div class="ess-gl-card"><div class="ess-gl-empty">📋 No guidelines uploaded for <strong>' +
				frappe.utils.escape_html(emp.company) + '</strong> yet. Please contact HR.</div></div>';
		} else {
			html += makeFileCard(g, emp.company);
		}
		$wrap.html(html);
		$wrap[0].addEventListener('contextmenu', function(e){ e.preventDefault(); });
	}

	function renderAdmin($wrap, d) {
		var guidelines = d.guidelines || [];
		var html = '<div class="ess-gl-header"><div><div class="ess-gl-title">Appointment Guidelines</div>' +
			'<div class="ess-gl-subtitle">Admin view — all companies</div></div>' +
			'<div class="ess-gl-badge"><div style="width:32px;height:32px;border-radius:50%;background:#3b5bdb;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff">AD</div>' +
			'<div><div class="ess-gl-badge-name">Administrator</div><div class="ess-gl-badge-co">All Companies</div></div></div></div>';

		if (!guidelines.length) {
			html += '<div class="ess-gl-card"><div class="ess-gl-empty">📋 No guidelines uploaded yet.</div></div>';
			$wrap.html(html); return;
		}

		if (guidelines.length > 1) {
			html += '<div class="ess-gl-tabs">';
			guidelines.forEach(function(g, i) {
				html += '<button class="ess-gl-tab' + (i===0?' active':'') + '" onclick="essTab(' + i + ')">' + frappe.utils.escape_html(g.company) + '</button>';
			});
			html += '</div>';
		}

		guidelines.forEach(function(g, i) {
			html += '<div class="ess-gl-admin-panel" id="ess-panel-' + i + '" style="' + (i===0?'':'display:none') + '">' + makeFileCard(g, g.company) + '</div>';
		});

		$wrap.html(html);
		$wrap[0].addEventListener('contextmenu', function(e){ e.preventDefault(); });

		window.essTab = function(idx) {
			$('.ess-gl-admin-panel').hide();
			$('#ess-panel-' + idx).show();
			$('.ess-gl-tab').removeClass('active').eq(idx).addClass('active');
		};
	}

	function makeFileCard(g, company) {
		var fileUrl = g.guideline_file;
		var ext = fileUrl.split('.').pop().toLowerCase();
		var date = g.effective_date ? frappe.datetime.str_to_user(g.effective_date) : '';
		var fullUrl = window.location.origin + fileUrl;
		var src = ext === 'pdf'
			? fullUrl + '#toolbar=0&navpanes=0&scrollbar=1'
			: 'https://view.officeapps.live.com/op/embed.aspx?src=' + encodeURIComponent(fullUrl);

		return '<div class="ess-gl-card">' +
			'<div class="ess-gl-card-hd">' +
			'<div class="ess-gl-card-title">📁 ' + frappe.utils.escape_html(g.title) +
			'<span style="font-size:11px;color:#9ca3af;font-weight:400">' + frappe.utils.escape_html(company) + (date?' · '+date:'') + '</span></div>' +
			'<div class="ess-gl-lock">🔒 View only — no download</div>' +
			'</div>' +
			'<div class="ess-gl-pdf-wrap">' +
			'<div class="ess-gl-pdf-overlay"></div>' +
			'<iframe class="ess-gl-pdf-frame" src="' + src + '" sandbox="allow-same-origin allow-scripts allow-forms"></iframe>' +
			'</div>' +
			'<div class="ess-gl-footer">🔒 Secured view — right-click, print and save are disabled.</div>' +
			'</div>';
	}

	function makeHeader(emp) {
		var initials = (emp.name||'U').split(' ').map(function(n){return n[0];}).join('').substring(0,2).toUpperCase();
		return '<div class="ess-gl-header">' +
			'<div><div class="ess-gl-title">Appointment Guidelines</div>' +
			'<div class="ess-gl-subtitle">Secure read-only document — downloading is disabled.</div></div>' +
			'<div class="ess-gl-badge"><div style="width:32px;height:32px;border-radius:50%;background:#3b5bdb;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff">' + initials + '</div>' +
			'<div><div class="ess-gl-badge-name">' + frappe.utils.escape_html(emp.name) + '</div>' +
			'<div class="ess-gl-badge-co">' + frappe.utils.escape_html(emp.company) + '</div></div></div></div>';
	}

	function showError($wrap, msg) {
		$wrap.html('<div class="ess-gl-header"><div class="ess-gl-title">Appointment Guidelines</div></div>' +
			'<div class="ess-gl-error">⚠️ ' + frappe.utils.escape_html(msg) + '</div>');
	}
};
