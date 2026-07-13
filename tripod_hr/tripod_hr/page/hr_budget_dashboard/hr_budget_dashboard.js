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
		'.hbd .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}' +
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
		'.hbd .loading{padding:40px;text-align:center;color:#6B7280}'
	).appendTo('head');

	var $body = $('<div class="hbd"><div class="loading">Loading…</div></div>').appendTo(page.body);

	function fmt(n) { return Math.round(n || 0).toLocaleString(); }
	function regPill(reg) {
		if (reg === 'UAE') return '<span class="pill u">UAE</span>';
		if (reg === 'KSA') return '<span class="pill k">KSA</span>';
		return '';
	}

	function activeTable(a) {
		var h = '<div class="card"><table><thead><tr>' +
			'<th>Unit</th><th>Head count</th><th>Salary / mo</th><th>CTC / mo</th>' +
			'<th>Salary / yr</th><th>CTC / yr</th><th>Region</th></tr></thead><tbody>';
		var tot = a.current_ctc || 0;
		a.rows.forEach(function (r) {
			var cls = r.kind === 'subtotal' ? 'sub' : (r.kind === 'grand' ? 'grand' : (r.kind === 'untagged' ? 'untag' : ''));
			var pctv = tot ? (r.ctc / tot * 100).toFixed(1) + '%' : '';
			h += '<tr class="' + cls + '"><td>' + r.unit + '</td><td>' + fmt(r.hc) + '</td><td>' +
				fmt(r.salary) + '</td><td>' + fmt(r.ctc) + '</td><td>' + fmt(r.salary_yr) + '</td><td>' +
				fmt(r.ctc_yr) + '</td><td>' + (r.kind === 'unit' ? regPill(r.region) : '') + '</td></tr>';
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

	function render(d) {
		var a = d.active, p = d.plan, rp = d.ramp;
		var projected = (a.current_ctc || 0) + (p.total_ctc || 0);
		var pct = a.current_ctc ? (p.total_ctc / a.current_ctc * 100).toFixed(1) : 0;
		var grand = a.rows.filter(function (r) { return r.kind === 'grand'; })[0] || { hc: 0 };

		var html = '<div class="kpis">' +
			kpi('Active headcount', fmt(grand.hc), '') +
			kpi('Monthly CTC', fmt(a.current_ctc), '') +
			kpi('Planned hires', fmt(p.rows.filter(function (r) { return r.kind === 'grand'; })[0].hc), '') +
			kpi('Projected CTC', fmt(projected), '+' + pct + '%') +
			'</div>';

		html += '<h2>1 · Active staff</h2><p class="note">Live from Employee master (status = Active).</p>' + activeTable(a);
		html += '<h2>2 · Budget increase — Jul–Dec 2026</h2><p class="note">Open positions in the Hiring Plan. % = share of current payroll added.</p>' + planTable(p, a.current_salary);
		html += '<h2>3 · Likely monthly payable — Jul–Dec</h2><p class="note">Current staff flat; open positions phase in by planned month (salary, cumulative).</p>' + rampTable(rp);

		$body.html(html);
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
