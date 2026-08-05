frappe.pages['hr-budget-dashboard'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'HR Budget Dashboard',
		single_column: true
	});

	var company_field = page.add_field({
		fieldname: 'company',
		label: 'Company',
		fieldtype: 'Select',
		options: [
			{ label: 'All (Tripod Media + Global)', value: 'All' },
			{ label: 'Tripod Media', value: 'Tripod Media FZ LLC' },
			{ label: 'Tripod Global', value: 'TRIPOD GLOBAL SHOPFIT MANUFACTURING COMPANY' }
		],
		default: 'All',
		change: function () { load(); }
	});

	page.add_inner_button('Refresh', function () { load(); });

	$('<style>').text(
		'.hbd{padding:22px 26px;max-width:1080px;margin:0 auto;color:#16233A;font-family:Inter,system-ui,sans-serif}' +
		'.hbd .kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:8px}' +
		'.hbd .kpi{background:#fff;border:1px solid #E5E3DC;border-radius:12px;padding:14px 16px}' +
		'.hbd .kpi .l{font-size:12px;color:#6B7280;font-weight:500}' +
		'.hbd .kpi .v{font-size:26px;font-weight:600;line-height:1.1;margin-top:5px}' +
		'.hbd .kpi .d{font-size:12px;margin-top:3px;font-weight:600;color:#B8863B}' +
		'.hbd h2{font-size:18px;font-weight:600;margin:30px 0 4px}' +
		'.hbd .note{color:#6B7280;font-size:12px;margin:0 0 12px}' +
		'.hbd .card{background:#fff;border:1px solid #E5E3DC;border-radius:12px;overflow:hidden}' +
		'.hbd table{width:100%;border-collapse:collapse;font-size:12.5px}' +
		'.hbd th,.hbd td{padding:8px 12px;text-align:right;white-space:nowrap}' +
		'.hbd th:first-child,.hbd td:first-child{text-align:left}' +
		'.hbd thead th{background:#16233A;color:#fff;font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.03em}' +
		'.hbd tbody td{border-bottom:1px solid #F0EEE8}' +
		'.hbd tr.sub td{background:#F5EBD6;font-weight:600}' +
		'.hbd tr.untag td{background:#FCEBEB;color:#A32D2D;font-weight:600}' +
		'.hbd tr.grand td{background:#16233A;color:#fff;font-weight:600;font-size:13px}' +
		'.hbd .pill{display:inline-block;font-size:10.5px;font-weight:600;padding:1px 8px;border-radius:20px}' +
		'.hbd .u{background:#E5EEF6;color:#2A5C8A}.hbd .k{background:#E2F1EA;color:#1B7A5A}' +
		'.hbd tr.dsg td{background:#FBFCFE;color:#3A4A63;font-size:12px;padding:6px 12px;border-bottom:1px solid #F5F4EF}' +
		'.hbd tr.dsg td:first-child{padding-left:30px}' +
		'.hbd .hclink{color:#185FA5;border-bottom:1px solid #185FA5;cursor:pointer}' +
		'.hbd .mvlink{color:#185FA5;border-bottom:1px solid #185FA5;cursor:pointer}' +
		'.hbd tr.mvsub td{background:#FBFCFE;font-size:11.5px;padding:5px 12px;border-bottom:1px solid #F5F4EF}' +
		'.hbd .chev{color:#9AA3B0;font-size:10px;margin-right:6px;cursor:pointer}' +
		'.hbd td.pos{color:#0F6E56}.hbd td.neg{color:#A32D2D}' +
		'.hbd .loading{padding:40px;text-align:center;color:#6B7280}'
	).appendTo('head');

	var $body = $('<div class="hbd"><div class="loading">Loading…</div></div>').appendTo(page.body);

	function fmt(n) { return Math.round(n || 0).toLocaleString(); }
	function regPill(reg) {
		if (reg === 'UAE') return '<span class="pill u">UAE</span>';
		if (reg === 'KSA') return '<span class="pill k">KSA</span>';
		return '';
	}

	function activeTable(a, dsg) {
		var h = '<div class="card"><table><thead><tr>' +
			'<th>Unit</th><th>Head count</th><th>Salary / mo</th><th>CTC / mo</th>' +
			'<th>Salary / yr</th><th>CTC / yr</th><th>Region</th></tr></thead><tbody>';
		var tot = a.current_ctc || 0;
		a.rows.forEach(function (r) {
			var cls = r.kind === 'subtotal' ? 'sub' : (r.kind === 'grand' ? 'grand' : (r.kind === 'untagged' ? 'untag' : ''));
			var pctv = tot ? (r.ctc / tot * 100).toFixed(1) + '%' : '';
			var kids = (r.kind === 'unit' || r.kind === 'untagged') ? (dsg && dsg[r.unit]) : null;
			var hasKids = kids && kids.length;

			var label = r.unit;
			var hcCell = fmt(r.hc);
			if (hasKids) {
				label = '<span class="chev" data-unit="' + r.unit + '">&#9654;</span>' + r.unit;
				hcCell = '<span class="hclink" data-unit="' + r.unit + '">' + fmt(r.hc) + '</span>';
			}

			h += '<tr class="' + cls + '"><td>' + label + '</td><td>' + hcCell + '</td><td>' +
				fmt(r.salary) + '</td><td>' + fmt(r.ctc) + '</td><td>' + fmt(r.salary_yr) + '</td><td>' +
				fmt(r.ctc_yr) + '</td><td>' + (r.kind === 'unit' ? regPill(r.region) : '') + '</td></tr>';

			if (hasKids) {
				kids.forEach(function (k) {
					h += '<tr class="dsg" data-parent="' + r.unit + '" style="display:none;">' +
						'<td>' + k.designation + '</td><td>' + (k.hc ? fmt(k.hc) : '–') + '</td><td>' +
						fmt(k.salary) + '</td><td>' + fmt(k.ctc) + '</td><td>' +
						fmt(k.salary * 12) + '</td><td>' + fmt(k.ctc * 12) + '</td><td></td></tr>';
				});
			}
		});
		return h + '</tbody></table></div>';
	}

	function planTable(p, curSalary) {
		var h = '<div class="card"><table><thead><tr>' +
			'<th>Unit</th><th>Head count</th><th>Salary / mo</th><th>CTC / mo</th><th>% incr</th><th>Region</th></tr></thead><tbody>';
		p.rows.forEach(function (r) {
			var cls = r.kind === 'subtotal' ? 'sub' : (r.kind === 'grand' ? 'grand' : '');
			var pctv = curSalary ? (r.salary / curSalary * 100).toFixed(1) + '%' : '';
			h += '<tr class="' + cls + '"><td>' + r.unit + '</td><td>' + fmt(r.hc) + '</td><td>' +
				fmt(r.salary) + '</td><td>' + fmt(r.ctc) + '</td><td>' + pctv + '</td><td>' +
				(r.kind === 'unit' ? regPill(r.region) : '') + '</td></tr>';
		});
		return h + '</tbody></table></div>';
	}

	function rampTable(rp) {
		var h = '<div class="card"><table><thead><tr><th>Line</th>';
		rp.months.forEach(function (m) { h += '<th>' + m + '</th>'; });
		h += '</tr></thead><tbody>';
		h += '<tr><td>Current staff</td>';
		rp.current.forEach(function (v) { h += '<td>' + fmt(v) + '</td>'; });
		h += '</tr>';
		rp.units.forEach(function (u) {
			h += '<tr><td>' + u.unit + '</td>';
			u.vals.forEach(function (v) { h += '<td>' + (v ? fmt(v) : '–') + '</td>'; });
			h += '</tr>';
		});
		h += '<tr class="sub"><td>Total payout</td>';
		rp.total.forEach(function (v) { h += '<td>' + fmt(v) + '</td>'; });
		h += '</tr><tr class="grand"><td>% increase</td>';
		rp.pct.forEach(function (v) { h += '<td>' + v + '%</td>'; });
		h += '</tr></tbody></table></div>';
		return h;
	}

	function movementTable(m) {
		var h = '<div class="card"><table><thead><tr>' +
			'<th>Month</th><th>Opening CTC</th><th>Joined</th><th>Added</th>' +
			'<th>Left</th><th>Removed</th><th>Closing CTC</th></tr></thead><tbody>';

		m.rows.forEach(function (r, i) {
			var jCell = r.joined
				? '<span class="mvlink" data-row="' + i + '" data-kind="j">' + fmt(r.joined) + '</span>'
				: '–';
			var lCell = r.left
				? '<span class="mvlink" data-row="' + i + '" data-kind="l">' + fmt(r.left) + '</span>'
				: '–';
			h += '<tr><td>' + r.month + '</td><td>' + fmt(r.opening) + '</td>' +
				'<td>' + jCell + '</td>' +
				'<td class="pos">' + (r.added ? '+' + fmt(r.added) : '–') + '</td>' +
				'<td>' + lCell + '</td>' +
				'<td class="neg">' + (r.removed ? '\u2212' + fmt(r.removed) : '–') + '</td>' +
				'<td>' + fmt(r.closing) + '</td></tr>';

			// hidden breakdown rows for joined
			if (r.joined) {
				h += '<tr class="mvsub" data-parent="' + i + '-j" style="display:none;">' +
					'<td></td><td style="text-align:right;color:#3A4A63;">Office Staff</td>' +
					'<td>' + fmt(r.joined_office) + '</td><td colspan="4"></td></tr>';
				h += '<tr class="mvsub" data-parent="' + i + '-j" style="display:none;">' +
					'<td></td><td style="text-align:right;color:#3A4A63;">Labour</td>' +
					'<td>' + fmt(r.joined_labour) + '</td><td colspan="4"></td></tr>';
			}
			// hidden breakdown rows for left
			if (r.left) {
				h += '<tr class="mvsub" data-parent="' + i + '-l" style="display:none;">' +
					'<td></td><td colspan="3"></td><td style="text-align:left;color:#3A4A63;">Office Staff ' + fmt(r.left_office) + '</td><td colspan="2"></td></tr>';
				h += '<tr class="mvsub" data-parent="' + i + '-l" style="display:none;">' +
					'<td></td><td colspan="3"></td><td style="text-align:left;color:#3A4A63;">Labour ' + fmt(r.left_labour) + '</td><td colspan="2"></td></tr>';
			}
		});

		h += '<tr class="grand"><td>NET</td><td></td><td>' + fmt(m.net_joined) + '</td><td>+' +
			fmt(m.net_added) + '</td><td>' + fmt(m.net_left) + '</td><td>\u2212' +
			fmt(m.net_removed) + '</td><td>' + fmt(m.closing) + '</td></tr>';

		h += '</tbody></table></div>';

		if (m.undated_leavers) {
			h += '<p class="note" style="color:#A32D2D;margin-top:8px;">' + m.undated_leavers +
				' employee(s) marked Left have no relieving date, so they are not in the Left column. ' +
				'Add the date on their Employee record to include them.</p>';
		}
		return h;
	}

	function render(d) {
		var a = d.active, p = d.plan, rp = d.ramp;
		var dsg = d.designations || {};
		var mv = d.movement;
		var projected = (a.current_ctc || 0) + (p.total_ctc || 0);
		var pct = a.current_ctc ? (p.total_ctc / a.current_ctc * 100).toFixed(1) : 0;
		var grand = a.rows.filter(function (r) { return r.kind === 'grand'; })[0] || { hc: 0 };

		var html = '<div class="kpis">' +
			kpi('Active headcount', fmt(grand.hc), '') +
			kpi('Monthly Salary', fmt(a.current_salary), '') +
			kpi('Monthly CTC', fmt(a.current_ctc), '') +
			kpi('Planned hires', fmt(p.rows.filter(function (r) { return r.kind === 'grand'; })[0].hc), '') +
			kpi('Projected CTC', fmt(projected), '+' + pct + '%') +
			'</div>';

		html += '<h2>1 · Active staff</h2><p class="note">Live from Employee master (status = Active). Click a head count to see its designations.</p>' + activeTable(a, dsg);
		// Sections 2 & 3 hidden for now (kept in code, can be restored):
		// html += '<h2>2 · Budget increase — Jul–Dec 2026</h2><p class="note">Open positions in the Hiring Plan. % = share of current payroll added.</p>' + planTable(p, a.current_salary);
		// html += '<h2>3 · Likely monthly payable — Jul–Dec</h2><p class="note">Current staff flat; open positions phase in by planned month (salary, cumulative).</p>' + rampTable(rp);

		if (mv && mv.rows && mv.rows.length) {
			html += '<h2>4 · Movement — joiners &amp; leavers</h2>' +
				'<p class="note">Last 6 months. Who joined, who left, and the effect on monthly CTC.</p>' +
				movementTable(mv);
		}

		$body.html(html);

		$body.find('.mvlink').on('click', function () {
			var key = $(this).attr('data-row') + '-' + $(this).attr('data-kind');
			var $subs = $body.find('tr.mvsub').filter(function () {
				return $(this).attr('data-parent') === key;
			});
			var showing = $subs.first().is(':visible');
			$subs.toggle(!showing);
		});

		$body.find('.hclink, .chev').on('click', function () {
			var unit = $(this).attr('data-unit');
			var $kids = $body.find('tr.dsg').filter(function () {
				return $(this).attr('data-parent') === unit;
			});
			var showing = $kids.first().is(':visible');
			$kids.toggle(!showing);
			$body.find('.chev').filter(function () {
				return $(this).attr('data-unit') === unit;
			}).html(showing ? '&#9654;' : '&#9660;');
		});
	}

	function kpi(l, v, d) {
		return '<div class="kpi"><div class="l">' + l + '</div><div class="v">' + v + '</div>' +
			(d ? '<div class="d">' + d + '</div>' : '<div class="d" style="color:#6B7280">&nbsp;</div>') + '</div>';
	}

	function load() {
		$body.html('<div class="loading">Loading…</div>');
		var c = company_field.get_value();
		frappe.call({
			method: 'tripod_hr.tripod_hr.page.hr_budget_dashboard.hr_budget_dashboard.get_budget_dashboard',
			args: { company: (c && c !== 'All') ? c : null },
			callback: function (r) {
				if (r.message) { render(r.message); }
				else { $body.html('<div class="loading">No data.</div>'); }
			}
		});
	}

	load();
};
