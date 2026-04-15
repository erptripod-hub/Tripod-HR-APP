frappe.pages['appraisal-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Appraisal Dashboard',
		single_column: true
	});

	page.add_inner_button('Refresh', function() { load_dashboard(); });

	$('<style>').text(
		'.ad{padding:20px;background:#f5f7f9;min-height:100vh}' +
		'.ad .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}' +
		'.ad .stat-card{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}' +
		'.ad .stat-card.pink{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%)}' +
		'.ad .stat-card.blue{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)}' +
		'.ad .stat-card.green{background:linear-gradient(135deg,#43e97b 0%,#38f9d7 100%)}' +
		'.ad .stat-card .label{font-size:11px;text-transform:uppercase;opacity:0.9;letter-spacing:0.5px;margin-bottom:8px}' +
		'.ad .stat-card .value{font-size:32px;font-weight:bold;line-height:1}' +
		'.ad .dept-card{background:#fff;border-radius:8px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.08);overflow:hidden}' +
		'.ad .dept-header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:18px 20px;display:flex;justify-content:space-between;align-items:center}' +
		'.ad .dept-header .name{font-size:16px;font-weight:bold}' +
		'.ad .dept-header .stats{display:flex;gap:20px;font-size:13px}' +
		'.ad table{width:100%;border-collapse:collapse}' +
		'.ad th{background:#f8f9fa;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#6c757d;font-weight:600;padding:10px 12px;text-align:left;border-bottom:2px solid #e9ecef}' +
		'.ad td{font-size:13px;padding:12px;border-bottom:1px solid #f1f3f5;vertical-align:middle}' +
		'.ad tr:last-child td{border-bottom:none}' +
		'.ad tr:hover td{background:#f8f9fa}' +
		'.ad .badge{display:inline-block;padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}' +
		'.ad .badge.success{background:#d4edda;color:#155724}' +
		'.ad .badge.warning{background:#fff3cd;color:#856404}' +
		'.ad .rating-badge{display:inline-block;padding:4px 12px;border-radius:12px;font-weight:bold;color:#fff}' +
		'.ad .empty{text-align:center;padding:60px 20px;color:#6c757d}' +
		'.ad .empty h4{margin-bottom:10px;font-size:16px}' +
		'.ad .empty p{font-size:13px;margin-bottom:20px}'
	).appendTo('head');

	$(wrapper).find('.page-content').html(
		'<div class="ad">' +
		'<div id="ad-stats"></div>' +
		'<div id="ad-content"></div>' +
		'</div>'
	);

	load_dashboard();

	function load_dashboard() {
		frappe.call({
			method: 'tripod_hr.tripod_hr.page.appraisal_dashboard.appraisal_dashboard.get_dashboard_data',
			callback: function(r) {
				if (r.message) {
					render_stats(r.message.stats);
					render_departments(r.message.departments);
				} else {
					render_empty();
				}
			},
			error: function(r) {
				console.error('Dashboard load error:', r);
				render_empty();
			}
		});
	}

	function render_stats(stats) {
		var html = '<div class="stats">';
		html += '<div class="stat-card"><div class="label">Total Appraisals</div><div class="value">' + (stats.total || 0) + '</div></div>';
		html += '<div class="stat-card pink"><div class="label">Pending</div><div class="value">' + (stats.pending || 0) + '</div></div>';
		html += '<div class="stat-card blue"><div class="label">Completed</div><div class="value">' + (stats.completed || 0) + '</div></div>';
		html += '<div class="stat-card green"><div class="label">Avg Rating</div><div class="value">' + (stats.avg_rating ? stats.avg_rating.toFixed(1) : '0.0') + '</div></div>';
		html += '</div>';
		document.getElementById('ad-stats').innerHTML = html;
	}

	function render_departments(departments) {
		if (!departments || departments.length === 0) {
			render_empty();
			return;
		}

		var html = '';
		departments.forEach(function(dept) {
			html += '<div class="dept-card">';
			html += '<div class="dept-header">';
			html += '<div class="name">📁 ' + dept.name + '</div>';
			html += '<div class="stats">';
			html += '<span>Total: ' + dept.total + '</span>';
			html += '<span>Completed: ' + dept.completed + '</span>';
			html += '<span>Avg: ' + dept.avg_rating.toFixed(1) + '</span>';
			html += '</div>';
			html += '</div>';
			html += '<table>';
			html += '<thead><tr><th>Employee</th><th>Cycle</th><th>Rating</th><th>Status</th><th>Action</th></tr></thead>';
			html += '<tbody>';
			
			dept.employees.forEach(function(emp) {
				// Show workflow state instead of generic status
				var workflowState = emp.workflow_state || 'Draft';
				var statusClass = workflowState === 'Completed' ? 'success' : 'warning';
				var statusBadge = '<span class="badge ' + statusClass + '">' + workflowState + '</span>';
				
				var rating = emp.overall_rating || 0;
				var ratingColor = rating >= 4 ? '#27ae60' : rating >= 3 ? '#f39c12' : '#e74c3c';
				var ratingBadge = emp.overall_rating ? 
					'<span class="rating-badge" style="background:' + ratingColor + '">' + parseFloat(emp.overall_rating).toFixed(1) + '</span>' : 
					'-';
				
				html += '<tr onclick="frappe.set_route(\'Form\',\'Performance Appraisal Form\',\'' + emp.name + '\')" style="cursor:pointer">';
				html += '<td><strong>' + emp.employee_name + '</strong></td>';
				html += '<td>' + (emp.appraisal_cycle || '-') + '</td>';
				html += '<td>' + ratingBadge + '</td>';
				html += '<td>' + statusBadge + '</td>';
				html += '<td><button class="btn btn-xs btn-primary" onclick="event.stopPropagation();frappe.set_route(\'Form\',\'Performance Appraisal Form\',\'' + emp.name + '\')">View</button></td>';
				html += '</tr>';
			});
			
			html += '</tbody></table></div>';
		});
		
		document.getElementById('ad-content').innerHTML = html;
	}

	function render_empty() {
		document.getElementById('ad-content').innerHTML = 
			'<div class="empty">' +
			'<h4>No Appraisals Found</h4>' +
			'<p>Create your first performance appraisal to get started!</p>' +
			'<button class="btn btn-primary btn-sm" onclick="frappe.new_doc(\'Performance Appraisal Form\')">Create New Appraisal</button>' +
			'</div>';
	}
};
