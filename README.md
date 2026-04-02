# Tripod HR

Custom HR Management App for Tripod - Performance Appraisals, Reviews and HR Workflows

## Features

### Performance Appraisal Form
- **Flexible Objectives**: HR can add unlimited objectives per employee
- **Complete Customization**: Different appraisals for different departments/roles
- **Multi-step Workflow**: HR → Manager → Employee → HR → Complete
- **Automatic Rating Calculation**: Overall rating auto-calculated from objective ratings
- **Email Notifications**: Automatic notifications at each workflow stage

## Installation

### Prerequisites
- ERPNext v14 or higher
- Frappe Framework
- HRMS app installed

### Steps

1. **Get the app from GitHub**
```bash
cd ~/frappe-bench
bench get-app https://github.com/YOUR-ORG/tripod_hr.git
```

2. **Install on your site**
```bash
bench --site your-site-name install-app tripod_hr
```

3. **Run migrations**
```bash
bench --site your-site-name migrate
```

4. **Clear cache**
```bash
bench --site your-site-name clear-cache
```

5. **Restart bench**
```bash
bench restart
```

## Manual Installation (If you have the app folder)

1. **Copy app to bench apps folder**
```bash
cp -r tripod_hr ~/frappe-bench/apps/
```

2. **Install app**
```bash
cd ~/frappe-bench
bench --site your-site-name install-app tripod_hr
```

3. **Complete setup**
```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
bench restart
```

## Usage

### Creating Performance Appraisal

1. Go to **HR > Performance Appraisal Form > New**
2. Select **Employee** (Department, Designation auto-filled)
3. Enter **Review Period** (e.g., "Q1 2026" or "Jan-Jun 2026")
4. Add **Objectives** - click "Add Row" to add multiple objectives:
   - Objective Number (e.g., 1, 2, 3)
   - Objective Title (e.g., "New Business Development")
   - Values/Competencies (e.g., "Proactivity, Client Engagement")
   - Role Specific Expectations (detailed text)
   - Consider Factors (what to evaluate)
   - Manager Comments (filled by manager)
   - Rating 1-5 (filled by manager)
5. Save as Draft

### Workflow Process

**Step 1: HR Creates Appraisal**
- HR creates the form with objectives
- Status: Draft
- Action: "Send to Manager"

**Step 2: Manager Reviews & Rates**
- Manager receives notification
- Manager adds comments and ratings for each objective
- Overall rating calculated automatically
- Manager adds overall comments
- Action: "Send to Employee"

**Step 3: Employee Reviews**
- Employee receives notification
- Employee can view their appraisal (read-only)
- Employee acknowledges by clicking "Return to HR"

**Step 4: HR Final Review**
- HR reviews completed appraisal
- HR selects decision: Increment/Promotion/No Change/PIP/etc.
- HR adds remarks
- Action: "Approve" (submits the document)

**Step 5: Completed**
- Document is submitted
- Employee receives email notification
- Appraisal is locked

### Rating Scale

| Rating | Score | Definition |
|--------|-------|------------|
| Outstanding | 5 | Exceptional achievement with outstanding initiative and results |
| Excellent | 4 | Consistently exceeds job requirements in most aspects |
| Good | 3 | Meets all job requirements (standard expectation) |
| Fair | 2 | Falls short of expectations, needs improvement |
| Poor | 1 | Unacceptable performance, fails to meet basic requirements |

### HR Decisions Available

- **Increment** - Salary increase
- **Promotion** - Role advancement
- **No Change** - Continue as-is
- **Performance Improvement Plan** - Support and review
- **Demotion** - Role/salary reduction
- **Transfer** - Department/location change
- **Separation** - Employment termination

## Permissions

### HR Manager
- Create appraisals
- Edit in Draft and With HR states
- Submit/Approve appraisals
- View all appraisals

### Employee (Manager Role)
- Edit appraisals in "With Manager" state
- Add ratings and comments
- Cannot create or approve

### Employee
- View own appraisals only
- Read-only access
- Can acknowledge in "With Employee" state

## Configuration

### Setting up Line Manager Auto-fetch

The system automatically fetches the line manager from the Employee master. Ensure:
1. Employee records have "Reports To" field filled
2. This will auto-populate "Line Manager" in appraisal

### Customizing Workflow

To modify the workflow:
1. Go to **Setup > Workflow > Performance Appraisal Workflow**
2. Edit states and transitions as needed
3. Save and clear cache

### Email Notifications

Email notifications are sent automatically:
- When appraisal moves to next stage
- When appraisal is completed
- Ensure email settings are configured in ERPNext

## Dashboard (Coming Soon)

Future updates will include:
- Appraisals by Status
- Pending Appraisals Table
- Average Ratings by Department
- Monthly Completion Trends

## Troubleshooting

### App not showing after installation
```bash
bench --site your-site-name clear-cache
bench restart
```

### Workflow not working
1. Check if Workflow is active: Setup > Workflow
2. Ensure users have correct roles assigned
3. Clear cache and retry

### Permissions issue
1. Go to Setup > Role Permissions Manager
2. Check "Performance Appraisal Form" permissions
3. Ensure HR Manager, Employee roles have correct access

## Support

For issues or questions:
- Create an issue on GitHub
- Contact: hr@tripod.com

## License

MIT

## Version

Current Version: 0.0.1

## Credits

Developed for Tripod HR Team
Built on Frappe Framework & ERPNext
