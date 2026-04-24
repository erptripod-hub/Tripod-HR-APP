frappe.pages['ess-guidelines'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Appointment Guidelines',
		single_column: true
	});

	// ── Styles ─────────────────────────────────────────────────────────────
	if (!document.getElementById('ess-gl-styles')) {
		$('<style id="ess-gl-styles">').text(`
			.ess-gl-wrap {
				max-width: 860px;
				margin: 30px auto;
				padding: 0 20px;
				font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
			}
			.ess-gl-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				margin-bottom: 24px;
			}
			.ess-gl-title {
				font-size: 22px;
				font-weight: 700;
				color: #1a1a2e;
			}
			.ess-gl-subtitle {
				font-size: 13px;
				color: #9ca3af;
				margin-top: 3px;
			}
			.ess-gl-company-badge {
				display: flex;
				align-items: center;
				gap: 8px;
				background: #fff;
				border: 1px solid #e5e7eb;
				border-radius: 8px;
				padding: 8px 14px;
			}
			.ess-gl-company-name {
				font-size: 12px;
				font-weight: 600;
				color: #1a1a2e;
			}
			.ess-gl-company-label {
				font-size: 10px;
				color: #9ca3af;
			}
			.ess-gl-card {
				background: #fff;
				border: 1px solid #e5e7eb;
				border-radius: 12px;
				overflow: hidden;
			}
			.ess-gl-card-header {
				padding: 16px 20px;
				border-bottom: 1px solid #f3f4f6;
				display: flex;
				align-items: center;
				justify-content: space-between;
			}
			.ess-gl-card-title {
				display: flex;
				align-items: center;
				gap: 10px;
				font-size: 14px;
				font-weight: 600;
				color: #1a1a2e;
			}
			.ess-gl-folder-icon {
				width: 36px;
				height: 36px;
				background: #dbeafe;
				border-radius: 8px;
				display: flex;
				align-items: center;
				justify-content: center;
			}
			.ess-gl-lock-badge {
				display: flex;
				align-items: center;
				gap: 6px;
				background: #fffbeb;
				border: 1px solid #fde68a;
				border-radius: 6px;
				padding: 5px 12px;
				font-size: 11px;
				font-weight: 600;
				color: #92400e;
			}
			.ess-gl-file-row {
				display: flex;
				align-items: center;
				padding: 18px 20px;
				gap: 14px;
			}
			.ess-gl-file-icon {
				width: 44px;
				height: 50px;
				background: #c0392b;
				border-radius: 6px;
				display: flex;
				align-items: center;
				justify-content: center;
				font-size: 10px;
				font-weight: 700;
				color: #fff;
				flex-shrink: 0;
				letter-spacing: 0.3px;
			}
			.ess-gl-file-icon.pdf { background: #c0392b; }
			.ess-gl-file-icon.docx { background: #2b5797; }
			.ess-gl-file-icon.xlsx { background: #1d6f42; }
			.ess-gl-file-name {
				font-size: 14px;
				font-weight: 600;
				color: #1a1a2e;
				margin-bottom: 3px;
			}
			.ess-gl-file-meta {
				font-size: 12px;
				color: #9ca3af;
			}
			.ess-gl-view-btn {
				margin-left: auto;
				padding: 9px 22px;
				font-size: 13px;
				font-weight: 600;
				border: 1.5px solid #bfdbfe;
				border-radius: 8px;
				background: #eff6ff;
				color: #1d4ed8;
				cursor: pointer;
				transition: all 0.15s;
				white-space: nowrap;
				flex-shrink: 0;
			}
			.ess-gl-view-btn:hover {
				background: #dbeafe;
				border-color: #93c5fd;
			}
			.ess-gl-footer {
				padding: 10px 20px;
				background: #fafbfc;
				border-top: 1px solid #f3f4f6;
				font-size: 11px;
				color: #9ca3af;
				display: flex;
				align-items: center;
				gap: 6px;
			}
			.ess-gl-viewer {
				margin-top: 14px;
				background: #fff;
				border: 1px solid #e5e7eb;
				border-radius: 12px;
				overflow: hidden;
			}
			.ess-gl-viewer-header {
				padding: 14px 20px;
				border-bottom: 1px solid #f3f4f6;
				display: flex;
				align-items: center;
				justify-content: space-between;
			}
			.ess-gl-viewer-title {
				font-size: 13px;
				font-weight: 600;
				color: #1a1a2e;
			}
			.ess-gl-close-btn {
				padding: 6px 16px;
				font-size: 12px;
				border: 1px solid #e5e7eb;
				border-radius: 6px;
				background: #fff;
				color: #374151;
				cursor: pointer;
				font-weight: 500;
			}
			.ess-gl-close-btn:hover { background: #f9fafb; }
			.ess-gl-viewer-body {
				padding: 16px;
			}
			.ess-gl-empty {
				padding: 60px 20px;
				text-align: center;
				color: #9ca3af;
				font-size: 14px;
			}
			.ess-gl-empty-icon {
				font-size: 40px;
				margin-bottom: 12px;
			}
			.ess-gl-error {
				background: #fef2f2;
				border: 1px solid #fecaca;
				border-radius: 8px;
				padding: 16px 20px;
				color: #991b1b;
				font-size: 13px;
				display: flex;
				align-items: center;
				gap: 8px;
			}
		`).appendTo('head');
	}

	// ── Render container ───────────────────────────────────────────────────
	var $body = $(wrapper).find('.page-content');
	$body.html('<div class="ess-gl-wrap"><div class="ess-gl-loading" style="padding:60px;text-align:center;color:#9ca3af">Loading your guidelines...</div></div>');
	var $wrap = $body.find('.ess-gl-wrap');

	// ── Fetch guideline for current employee ───────────────────────────────
	frappe.call({
		method: 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.get_my_guideline',
		callback: function(r) {
			if (!r || !r.message) {
				showError($wrap, 'Could not load guidelines. Please try again.');
				return;
			}

			var data = r.message;

			if (!data.success) {
				showError($wrap, data.error || 'Unable to load your guidelines.');
				return;
			}

			renderPage($wrap, data);
		},
		error: function() {
			showError($wrap, 'Server error. Please refresh and try again.');
		}
	});

	function renderPage($wrap, data) {
		var emp = data.employee;
		var g = data.guideline;

		// Header
		var initials = emp.name ? emp.name.split(' ').map(function(n){ return n[0]; }).join('').substring(0,2).toUpperCase() : 'AA';
		var headerHtml =
			'<div class="ess-gl-header">' +
				'<div>' +
					'<div class="ess-gl-title">Appointment Guidelines</div>' +
					'<div class="ess-gl-subtitle">Read-only secure folder — files can be viewed in-browser only. Downloading is disabled.</div>' +
				'</div>' +
				'<div class="ess-gl-company-badge">' +
					'<div style="width:32px;height:32px;border-radius:50%;background:#3b5bdb;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff">' + initials + '</div>' +
					'<div>' +
						'<div class="ess-gl-company-name">' + frappe.utils.escape_html(emp.name) + '</div>' +
						'<div class="ess-gl-company-label">' + frappe.utils.escape_html(emp.company) + '</div>' +
					'</div>' +
				'</div>' +
			'</div>';

		// Card
		var cardHtml;
		if (!g) {
			cardHtml =
				'<div class="ess-gl-card">' +
					'<div class="ess-gl-card-header">' +
						'<div class="ess-gl-card-title">' +
							'<div class="ess-gl-folder-icon">📁</div>' +
							'Guidelines Folder' +
						'</div>' +
						'<div class="ess-gl-lock-badge">🔒 No download</div>' +
					'</div>' +
					'<div class="ess-gl-empty">' +
						'<div class="ess-gl-empty-icon">📋</div>' +
						'No guidelines have been uploaded for <strong>' + frappe.utils.escape_html(emp.company) + '</strong> yet.<br>' +
						'<span style="font-size:12px">Please contact HR.</span>' +
					'</div>' +
				'</div>';
		} else {
			var fileUrl = g.guideline_file || '';
			var fileName = fileUrl ? fileUrl.split('/').pop() : 'Guideline File';
			var ext = fileName.split('.').pop().toLowerCase();
			var extLabel = ext.toUpperCase();
			var date = g.effective_date ? frappe.datetime.str_to_user(g.effective_date) : '';

			cardHtml =
				'<div class="ess-gl-card">' +
					'<div class="ess-gl-card-header">' +
						'<div class="ess-gl-card-title">' +
							'<div class="ess-gl-folder-icon">📁</div>' +
							'Guidelines Folder' +
						'</div>' +
						'<div class="ess-gl-lock-badge">🔒 No download</div>' +
					'</div>' +
					'<div class="ess-gl-file-row">' +
						'<div class="ess-gl-file-icon ' + ext + '">' + extLabel + '</div>' +
						'<div>' +
							'<div class="ess-gl-file-name">' + frappe.utils.escape_html(g.title) + '</div>' +
							'<div class="ess-gl-file-meta">' + frappe.utils.escape_html(emp.company) + (date ? ' · Effective ' + date : '') + '</div>' +
						'</div>' +
						(fileUrl
							? '<button class="ess-gl-view-btn" id="ess-view-btn">View file</button>'
							: '<span style="font-size:12px;color:#d1d5db;margin-left:auto">No file attached</span>'
						) +
					'</div>' +
					'<div class="ess-gl-footer">🔒 Files open in a secure in-browser viewer. Right-click, print and save are disabled. Contact HR to change access.</div>' +
				'</div>' +
				'<div id="ess-viewer" style="display:none"></div>';
		}

		$wrap.html(headerHtml + cardHtml);

		// View button handler
		if (g && g.guideline_file) {
			$wrap.find('#ess-view-btn').on('click', function() {
				openViewer(g.guideline_file, g.title);
			});
		}
	}

	function openViewer(fileUrl, title) {
		var ext = fileUrl.split('.').pop().toLowerCase();
		var fullUrl = window.location.origin + fileUrl;
		var viewerContent;

		if (ext === 'pdf') {
			viewerContent =
				'<div style="position:relative;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;">' +
				'<div style="position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none"></div>' +
				'<iframe src="' + fullUrl + '#toolbar=0&navpanes=0&scrollbar=1" style="width:100%;height:650px;border:none;display:block"></iframe>' +
				'</div>';
		} else {
			var officeUrl = 'https://view.officeapps.live.com/op/embed.aspx?src=' + encodeURIComponent(fullUrl);
			viewerContent =
				'<div style="position:relative;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;">' +
				'<div style="position:absolute;top:0;left:0;right:0;bottom:0;z-index:10;pointer-events:none"></div>' +
				'<iframe src="' + officeUrl + '" style="width:100%;height:600px;border:none;display:block"></iframe>' +
				'</div>' +
				'<div style="margin-top:8px;font-size:11px;color:#9ca3af;text-align:center">Note: For best inline viewing, please use PDF format.</div>';
		}

		var html =
			'<div class="ess-gl-viewer">' +
				'<div class="ess-gl-viewer-header">' +
					'<div class="ess-gl-viewer-title">' + frappe.utils.escape_html(title) + '</div>' +
					'<div style="display:flex;align-items:center;gap:10px">' +
						'<span class="ess-gl-lock-badge" style="font-size:10px">🔒 View only</span>' +
						'<button class="ess-gl-close-btn" id="ess-close-btn">Close</button>' +
					'</div>' +
				'</div>' +
				'<div class="ess-gl-viewer-body">' + viewerContent + '</div>' +
			'</div>';

		var $viewer = $('#ess-viewer');
		$viewer.html(html).show();
		$viewer[0].scrollIntoView({behavior: 'smooth', block: 'nearest'});

		$viewer.find('#ess-close-btn').on('click', function() {
			$viewer.hide().html('');
		});

		// Block right click on viewer
		$viewer[0].addEventListener('contextmenu', function(e) { e.preventDefault(); });
	}

	function showError($wrap, msg) {
		$wrap.html(
			'<div class="ess-gl-header"><div class="ess-gl-title">Appointment Guidelines</div></div>' +
			'<div class="ess-gl-error">⚠️ ' + frappe.utils.escape_html(msg) + '</div>'
		);
	}
};
