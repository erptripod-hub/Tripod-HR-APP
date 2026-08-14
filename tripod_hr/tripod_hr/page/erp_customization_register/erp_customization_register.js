/* ERP Customization Register
 * Approval is set once. Every later change appends itself from the site hooks,
 * the git webhook, or the migration diff.
 * CSS is scoped under .ecr-root to avoid collisions with Bootstrap and desk styles.
 */

frappe.pages['erp-customization-register'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'ERP Customization Register',
		single_column: true
	});

	const state = { site: 'all', status: '', module: '', search: '', data: null };

	page.set_primary_action('Run discovery scan', () => run_discovery(state, page), 'refresh');
	page.add_menu_item('Preview discovery (read only)', () => preview_discovery());
	page.add_menu_item('Last migration diff', () => show_migration_diff());

	$(wrapper).find('.layout-main-section').append(`
		<div class="ecr-root">
			<style>
			.ecr-root{font-size:13px;color:#16191d}
			.ecr-root .ecr-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:4px 0 16px}
			.ecr-root .ecr-kpi{background:#fff;border:1px solid #e3e6ea;border-radius:8px;padding:13px 15px;cursor:pointer}
			.ecr-root .ecr-kpi:hover{border-color:#c9ced6}
			.ecr-root .ecr-kpi.on{border-color:#16191d;box-shadow:inset 0 0 0 1px #16191d}
			.ecr-root .ecr-kpi .l{font-size:11px;color:#858c96}
			.ecr-root .ecr-kpi .v{font-size:25px;font-weight:600;margin-top:5px;line-height:1.1}
			.ecr-root .ecr-kpi .s{font-size:11px;color:#858c96;margin-top:3px}
			.ecr-root .v-ok{color:#1d7a5f}.ecr-root .v-bad{color:#a52d2d}
			.ecr-root .ecr-grid{display:grid;grid-template-columns:1.85fr 1fr;gap:14px}
			.ecr-root .ecr-card{background:#fff;border:1px solid #e3e6ea;border-radius:8px;overflow:hidden}
			.ecr-root .ecr-head{padding:11px 15px;border-bottom:1px solid #eef0f3;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
			.ecr-root .ecr-head h3{font-size:13px;font-weight:600;margin:0}
			.ecr-root .ecr-head .hint{font-size:11px;color:#858c96;margin-top:2px}
			.ecr-root .ecr-tools{display:flex;gap:7px;padding:9px 15px;border-bottom:1px solid #eef0f3;flex-wrap:wrap;align-items:center}
			.ecr-root .ecr-tools input,.ecr-root .ecr-tools select{font-size:12px;padding:6px 9px;border:1px solid #e3e6ea;border-radius:6px;background:#fff;height:auto}
			.ecr-root .ecr-tools input{flex:1;min-width:150px}
			.ecr-root .ecr-chip{font-size:11px;padding:5px 10px;border:1px solid #e3e6ea;border-radius:20px;background:#fff;color:#4a5058;cursor:pointer}
			.ecr-root .ecr-chip.on{background:#16191d;color:#fff;border-color:#16191d}
			.ecr-root .ecr-rows{max-height:560px;overflow-y:auto}
			.ecr-root .ecr-row{display:grid;grid-template-columns:8px minmax(0,1fr) 176px 92px;gap:11px;align-items:center;padding:11px 15px;border-bottom:1px solid #eef0f3;cursor:pointer}
			.ecr-root .ecr-row:hover{background:#fafbfc}
			.ecr-root .ecr-dot{width:7px;height:7px;border-radius:50%}
			.ecr-root .ecr-nm{font-size:13px;font-weight:500;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
			.ecr-root .ecr-meta{font-size:11px;color:#858c96;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
			.ecr-root .ecr-tag{font-size:10px;padding:2px 7px;border-radius:4px;font-weight:600}
			.ecr-root .t-ok{background:#e8f4ef;color:#1d7a5f}.ecr-root .t-bad{background:#fbeaea;color:#a52d2d}
			.ecr-root .t-git{background:#eeecf7;color:#4a3f8f}.ecr-root .t-site{background:#eaf0f8;color:#3c5a8a}
			.ecr-root .ecr-people{display:flex;flex-direction:column;gap:3px;font-size:11px;color:#858c96}
			.ecr-root .ecr-people b{font-weight:500;color:#4a5058}
			.ecr-root .ecr-when{text-align:right;font-size:11px;color:#858c96}
			.ecr-root .ecr-when .c{font-weight:500;color:#4a5058}
			.ecr-root .ecr-feed{max-height:512px;overflow-y:auto;padding:4px 15px}
			.ecr-root .ecr-f{display:flex;gap:9px;padding:11px 0;border-bottom:1px solid #eef0f3}
			.ecr-root .ecr-fi{width:24px;height:24px;border-radius:5px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;font-weight:700;margin-top:1px}
			.ecr-root .ecr-ft{font-size:12px;line-height:1.45}
			.ecr-root .ecr-fd{font-size:11px;color:#858c96;margin-top:2px;font-family:monospace}
			.ecr-root .ecr-fm{font-size:10px;color:#a8aeb7;margin-top:3px}
			.ecr-root .ecr-mods{margin-top:14px;background:#fff;border:1px solid #e3e6ea;border-radius:8px;padding:15px}
			.ecr-root .ecr-mgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px 22px}
			.ecr-root .ecr-bar{height:5px;background:#edeff2;border-radius:3px;overflow:hidden;display:flex}
			.ecr-root .ecr-bar i{height:100%;display:block}
			.ecr-root .ecr-empty{padding:34px 15px;text-align:center;color:#858c96;font-size:12px}
			@media(max-width:1080px){.ecr-root .ecr-kpis{grid-template-columns:repeat(2,1fr)}.ecr-root .ecr-grid{grid-template-columns:1fr}.ecr-root .ecr-mgrid{grid-template-columns:repeat(2,1fr)}}
			</style>
			<div class="ecr-kpis" id="ecr-kpis"></div>
			<div class="ecr-grid">
				<div class="ecr-card">
					<div class="ecr-head">
						<div><h3>Register</h3><div class="hint">Auto-created on first push or first save — you only add the two names</div></div>
						<div style="font-size:11px;color:#858c96" id="ecr-count"></div>
					</div>
					<div class="ecr-tools">
						<input id="ecr-q" placeholder="Search name, app, module…">
						<select id="ecr-mod"><option value="">All modules</option></select>
						<select id="ecr-site"><option value="all">All sites</option></select>
						<span class="ecr-chip on" data-f="">All</span>
						<span class="ecr-chip" data-f="Needs Names">Needs names</span>
						<span class="ecr-chip" data-f="Registered">Registered</span>
					</div>
					<div class="ecr-rows" id="ecr-rows"></div>
				</div>
				<div class="ecr-card">
					<div class="ecr-head"><div><h3>Change log</h3><div class="hint">Site hooks, git pushes and migration diffs</div></div></div>
					<div class="ecr-feed" id="ecr-feed"></div>
				</div>
			</div>
			<div class="ecr-mods">
				<h3 style="font-size:13px;font-weight:600;margin:0">Coverage by module</h3>
				<div class="hint" style="font-size:11px;color:#858c96;margin:2px 0 14px">Share carrying a requester and an approver</div>
				<div class="ecr-mgrid" id="ecr-mgrid"></div>
			</div>
		</div>
	`);

	const $root = $(wrapper).find('.ecr-root');

	$root.on('click', '.ecr-chip', function () {
		$root.find('.ecr-chip').removeClass('on');
		$(this).addClass('on');
		state.status = $(this).data('f') || '';
		load(state, $root);
	});
	$root.on('click', '.ecr-kpi[data-k]', function () {
		const k = $(this).data('k');
		state.status = state.status === k ? '' : k;
		$root.find('.ecr-chip').removeClass('on').filter(function () {
			return ($(this).data('f') || '') === state.status;
		}).addClass('on');
		load(state, $root);
	});
	$root.find('#ecr-q').on('input', frappe.utils.debounce(function () {
		state.search = $(this).val();
		load(state, $root);
	}, 350));
	$root.find('#ecr-mod').on('change', function () { state.module = $(this).val(); load(state, $root); });
	$root.find('#ecr-site').on('change', function () { state.site = $(this).val(); load(state, $root); });
	$root.on('click', '.ecr-row', function () { open_drawer($(this).data('name'), state, $root); });

	load(state, $root);
};

function ago(dt) {
	if (!dt) return '—';
	return frappe.datetime.comment_when(dt, true);
}

function initials(name) {
	if (!name) return '?';
	return name.replace(/@.*/, '').split(/[\s._]+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

function esc(s) { return frappe.utils.escape_html(s == null ? '' : String(s)); }

function load(state, $root) {
	frappe.call({
		method: 'tripod_hr.registry.api.get_dashboard',
		args: { site: state.site, module: state.module, status: state.status, search: state.search },
		callback: r => {
			if (!r.message) return;
			state.data = r.message;
			render(r.message, state, $root);
		}
	});
}

function render(d, state, $root) {
	const k = d.kpi;
	const pct = k.total ? Math.round(k.registered / k.total * 100) : 0;
	$root.find('#ecr-kpis').html(`
		<div class="ecr-kpi"><div class="l">Customizations</div><div class="v">${k.total}</div><div class="s">${Object.keys(d.coverage).length} modules</div></div>
		<div class="ecr-kpi ${state.status === 'Registered' ? 'on' : ''}" data-k="Registered"><div class="l">Registered</div><div class="v v-ok">${k.registered}</div><div class="s">${pct}% documented</div></div>
		<div class="ecr-kpi ${state.status === 'Needs Names' ? 'on' : ''}" data-k="Needs Names"><div class="l">Needs names</div><div class="v v-bad">${k.needs_names}</div><div class="s">assign requester and approver</div></div>
		<div class="ecr-kpi"><div class="l">Changes logged</div><div class="v">${k.changes_week}</div><div class="s">${k.changes_today} today · this week</div></div>
	`);

	$root.find('#ecr-count').text(`${d.rows.length} shown`);
	$root.find('#ecr-rows').html(d.rows.length ? d.rows.map(r => {
		const reg = r.registration_status === 'Registered';
		return `<div class="ecr-row" data-name="${esc(r.name)}">
			<span class="ecr-dot" style="background:${reg ? '#1d7a5f' : '#a52d2d'}"></span>
			<div>
				<div class="ecr-nm">${esc(r.customization_name)}
					${reg ? '' : '<span class="ecr-tag t-bad">Needs names</span>'}
					${r.artefact_type === 'Print Format' ? '<span class="ecr-tag t-site">Not in git</span>' : ''}
					${r.is_active ? '' : '<span class="ecr-tag t-bad">Inactive</span>'}
				</div>
				<div class="ecr-meta">${esc(r.module || '—')} · ${esc(r.app_name || '—')} · ${esc(r.artefact_type || '—')} · ${esc(r.site_name || '')}</div>
			</div>
			<div class="ecr-people">
				<span>req <b>${esc(r.requested_by || 'not set')}</b></span>
				${reg ? `<span>appr <b>${esc(r.approved_by)}</b></span>` : '<span style="color:#a52d2d">approver not set</span>'}
			</div>
			<div class="ecr-when"><div class="c">${r.change_count || 0} changes</div><div>${ago(r.last_changed_on)}</div></div>
		</div>`;
	}).join('') : '<div class="ecr-empty">Nothing matches this filter. Run a discovery scan to seed the register.</div>');

	$root.find('#ecr-feed').html(d.feed.length ? d.feed.map(f => {
		const git = f.change_source === 'Git';
		const mig = f.change_source === 'Migration';
		const letter = git ? 'G' : mig ? 'M' : 'S';
		const bg = git ? '#eeecf7' : mig ? '#fbf1de' : '#eaf0f8';
		const fg = git ? '#4a3f8f' : mig ? '#9a6206' : '#3c5a8a';
		const verb = git ? 'pushed to' : mig ? 'migration changed' : 'saved on site';
		return `<div class="ecr-f"><div class="ecr-fi" style="background:${bg};color:${fg}">${letter}</div>
			<div><div class="ecr-ft"><b>${esc(f.changed_by)}</b> ${verb} ${esc(f.customization_title || f.artefact_name)}</div>
			<div class="ecr-fd">${esc(f.change_detail || '')}${f.reference ? ' · ' + esc(f.reference) : ''}</div>
			<div class="ecr-fm">${esc(f.artefact_type || '')} · ${esc(f.site_name || '')} · ${ago(f.change_time)}</div></div></div>`;
	}).join('') : '<div class="ecr-empty">No changes logged yet.</div>');

	const mods = Object.keys(d.coverage).sort();
	$root.find('#ecr-mgrid').html(mods.map(m => {
		const c = d.coverage[m];
		const p = c.total ? Math.round(c.registered / c.total * 100) : 0;
		const col = p >= 90 ? '#1d7a5f' : p >= 75 ? '#9a6206' : '#a52d2d';
		return `<div>
			<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px">
				<span style="font-size:12px;font-weight:500">${esc(m)}</span>
				<span style="font-size:12px;font-weight:600;color:${col}">${p}%</span></div>
			<div class="ecr-bar"><i style="background:#1d7a5f;width:${p}%"></i><i style="background:#d05b5b;width:${100 - p}%"></i></div>
			<div style="font-size:11px;color:#858c96;margin-top:5px">${c.registered} registered · ${c.total - c.registered} need names</div>
		</div>`;
	}).join(''));

	const $mod = $root.find('#ecr-mod');
	if ($mod.find('option').length <= 1) {
		$mod.append(mods.map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join(''));
		$mod.val(state.module || '');
	}
	const $site = $root.find('#ecr-site');
	if ($site.find('option').length <= 1 && d.sites && d.sites.length) {
		$site.append(d.sites.map(s => `<option value="${esc(s)}">${esc(s)}</option>`).join(''));
		$site.val(state.site);
	}
}

function open_drawer(name, state, $root) {
	frappe.call({
		method: 'tripod_hr.registry.api.get_customization',
		args: { name: name },
		callback: r => {
			if (!r.message) return;
			const doc = r.message.doc;
			const history = r.message.history || [];
			const registered = doc.registration_status === 'Registered';

			const d = new frappe.ui.Dialog({
				title: doc.customization_name,
				size: 'large',
				fields: [{ fieldtype: 'HTML', fieldname: 'body' }]
			});

			const artefacts = (doc.artefacts || []).map(a =>
				`<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #eef0f3">
					<div><div style="font-family:monospace;font-size:11px">${esc(a.artefact_name)}</div>
					<div style="font-size:10px;color:#858c96;margin-top:2px">${esc(a.artefact_type)}${a.target_doctype ? ' → ' + esc(a.target_doctype) : ''}</div></div>
					<div style="font-size:11px;color:#858c96;text-align:right">${a.in_git ? 'in git' : 'db only'}</div>
				</div>`).join('') || '<div style="font-size:12px;color:#858c96">No artefacts linked.</div>';

			const hist = history.map(h => {
				const git = h.change_source === 'Git';
				const mig = h.change_source === 'Migration';
				const letter = git ? 'G' : mig ? 'M' : 'S';
				const bg = git ? '#eeecf7' : mig ? '#fbf1de' : '#eaf0f8';
				const fg = git ? '#4a3f8f' : mig ? '#9a6206' : '#3c5a8a';
				return `<div style="display:grid;grid-template-columns:22px 1fr;gap:9px;padding:10px 0;border-bottom:1px solid #eef0f3">
					<div style="width:20px;height:20px;border-radius:4px;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;background:${bg};color:${fg}">${letter}</div>
					<div><div style="font-size:12px"><b>${esc(h.changed_by)}</b> · ${esc(h.change_source)}</div>
					<div style="font-family:monospace;font-size:11px;color:#858c96;margin-top:2px">${esc(h.change_detail || '')}${h.reference ? ' · ' + esc(h.reference) : ''}</div>
					<div style="font-size:10px;color:#a8aeb7;margin-top:3px">${ago(h.change_time)}</div></div></div>`;
			}).join('') || '<div style="font-size:12px;color:#858c96">No changes logged yet.</div>';

			const approval = registered ? `
				<div style="display:grid;grid-template-columns:120px 1fr;gap:6px 12px;font-size:12px">
					<span style="color:#858c96">Requested by</span><span>${esc(doc.requested_by)}</span>
					<span style="color:#858c96">Approved by</span><span>${esc(doc.approved_by)}</span>
					<span style="color:#858c96">Approved on</span><span>${esc(doc.approved_on)}</span>
					<span style="color:#858c96">Reference</span><span>${esc(doc.approval_reference || '—')}</span>
				</div>
				<div style="font-size:11px;color:#858c96;margin-top:9px;padding-top:9px;border-top:1px solid #eef0f3">
					Locked. Later changes append to the history below; no re-approval is requested.</div>`
				: `<div id="ecr-approve-slot"></div>
				<div style="font-size:11px;color:#858c96;margin-top:9px">Auto-created by ${esc(doc.last_change_source || 'discovery')}. Set the two names once — it will not ask again.</div>`;

			d.fields_dict.body.$wrapper.html(`
				<div style="font-size:11px;color:#858c96;margin-bottom:14px">
					${esc(doc.name)} · ${esc(doc.module || '—')} · ${esc(doc.app_name || '—')} · ${esc(doc.site_name || '')}</div>
				<div style="margin-bottom:18px"><div style="font-size:11px;color:#858c96;text-transform:uppercase;margin-bottom:9px">Approval — set once</div>${approval}</div>
				<div style="margin-bottom:18px"><div style="font-size:11px;color:#858c96;text-transform:uppercase;margin-bottom:9px">Linked artefacts (${(doc.artefacts || []).length})</div>${artefacts}</div>
				<div><div style="font-size:11px;color:#858c96;text-transform:uppercase;margin-bottom:9px">Change history (${history.length}) — logged automatically</div>${hist}</div>
			`);

			if (!registered) {
				const req = frappe.ui.form.make_control({
					parent: d.fields_dict.body.$wrapper.find('#ecr-approve-slot'),
					df: { fieldtype: 'Link', options: 'User', label: 'Requested by', reqd: 1, fieldname: 'req' },
					render_input: true
				});
				const app = frappe.ui.form.make_control({
					parent: d.fields_dict.body.$wrapper.find('#ecr-approve-slot'),
					df: { fieldtype: 'Link', options: 'User', label: 'Approved by', reqd: 1, fieldname: 'app' },
					render_input: true
				});
				const ref = frappe.ui.form.make_control({
					parent: d.fields_dict.body.$wrapper.find('#ecr-approve-slot'),
					df: { fieldtype: 'Small Text', label: 'Approval reference', fieldname: 'ref' },
					render_input: true
				});
				if (doc.requested_by) req.set_value(doc.requested_by);

				d.set_primary_action('Save names', () => {
					const rv = req.get_value(), av = app.get_value();
					if (!rv || !av) {
						frappe.msgprint('Both a requester and an approver are needed.');
						return;
					}
					frappe.call({
						method: 'tripod_hr.tripod_hr.doctype.erp_customization.erp_customization.set_approval',
						args: { customization: doc.name, requested_by: rv, approved_by: av, approval_reference: ref.get_value() },
						callback: () => {
							frappe.show_alert({ message: 'Registered', indicator: 'green' });
							d.hide();
							load(state, $root);
						}
					});
				});
			}
			d.show();
		}
	});
}

function preview_discovery() {
	frappe.call({
		method: 'tripod_hr.registry.discovery.preview',
		freeze: true,
		freeze_message: 'Scanning site…',
		callback: r => {
			const m = r.message || {};
			const rows = Object.keys(m.by_app || {}).sort().map(a =>
				`<tr><td style="padding:4px 10px 4px 0">${esc(a)}</td><td style="text-align:right">${m.by_app[a].total}</td><td style="text-align:right;color:#a52d2d">${m.by_app[a].new}</td></tr>`).join('');
			frappe.msgprint({
				title: 'Discovery preview (nothing created)',
				message: `<p>Found <b>${m.total_found}</b> artefacts. Already registered: <b>${m.already_registered}</b>. Would create: <b>${m.would_create}</b>.</p>
					<table style="width:100%;font-size:12px"><tr><th style="text-align:left">App</th><th style="text-align:right">Found</th><th style="text-align:right">New</th></tr>${rows}</table>`,
				wide: true
			});
		}
	});
}

function run_discovery(state, page) {
	frappe.confirm('Scan this site and create register entries for anything not yet tracked?', () => {
		frappe.call({
			method: 'tripod_hr.registry.discovery.run_discovery',
			args: { log_new: 1 },
			freeze: true,
			freeze_message: 'Scanning site…',
			callback: r => {
				const m = r.message || {};
				frappe.show_alert({ message: `Scanned ${m.scanned}, created ${m.created}`, indicator: 'green' });
				page.wrapper.find('.ecr-root').length && load(state, page.wrapper.find('.ecr-root'));
			}
		});
	});
}

function show_migration_diff() {
	frappe.call({
		method: 'tripod_hr.registry.migration.last_migration_diff',
		callback: r => {
			const m = r.message || {};
			if (!m.at) {
				frappe.msgprint('No migration diff recorded yet. One is taken automatically on the next bench migrate.');
				return;
			}
			const alerts = (m.alerts || []).map(a =>
				`<li><b>${esc(a.entry.type)}</b> ${esc(a.entry.name)} — ${esc(a.note)} (${esc(a.kind)})</li>`).join('');
			frappe.msgprint({
				title: 'Last migration diff · ' + esc(m.at),
				message: `<p>Ours: <b>${m.added_ours}</b> added, <b>${m.changed_ours}</b> changed, <b>${m.removed}</b> removed.<br>
					Framework: ${m.framework_added} added, ${m.framework_changed} changed.</p>
					${alerts ? '<p><b>Watchlist alerts</b></p><ul>' + alerts + '</ul>' : '<p>No watchlist alerts.</p>'}`,
				wide: true
			});
		}
	});
}
