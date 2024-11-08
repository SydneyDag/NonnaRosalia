document.addEventListener('DOMContentLoaded', function() {
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const territorySelect = document.getElementById('territory');
    const generateReportBtn = document.getElementById('generateReport');
    
    const reportsTable = $('#reportsTable').DataTable({
        columns: [
            { 
                data: 'delivery_date',
                render: function(data) {
                    return new Date(data).toLocaleDateString();
                }
            },
            { data: 'total_cases' },
            { 
                data: 'total_cost',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            },
            { 
                data: 'payment_cash',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            },
            { 
                data: 'payment_check',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            },
            { 
                data: 'payment_credit',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            },
            { 
                data: 'payment_received',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            },
            {
                data: 'outstanding',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            }
        ],
        order: [[0, 'desc']],
        footerCallback: function(row, data, start, end, display) {
            const api = this.api();

            // Calculate column totals
            const totalCases = api.column(1).data().reduce((a, b) => a + (b || 0), 0);
            const totalCost = api.column(2).data().reduce((a, b) => a + parseFloat(b || 0), 0);
            const totalCash = api.column(3).data().reduce((a, b) => a + parseFloat(b || 0), 0);
            const totalCheck = api.column(4).data().reduce((a, b) => a + parseFloat(b || 0), 0);
            const totalCredit = api.column(5).data().reduce((a, b) => a + parseFloat(b || 0), 0);
            const totalPayments = api.column(6).data().reduce((a, b) => a + parseFloat(b || 0), 0);
            const totalOutstanding = api.column(7).data().reduce((a, b) => a + parseFloat(b || 0), 0);

            // Update footer cells
            document.getElementById('tableTotalCases').textContent = totalCases;
            document.getElementById('tableTotalCost').textContent = `$${totalCost.toFixed(2)}`;
            document.getElementById('tableTotalCash').textContent = `$${totalCash.toFixed(2)}`;
            document.getElementById('tableTotalCheck').textContent = `$${totalCheck.toFixed(2)}`;
            document.getElementById('tableTotalCredit').textContent = `$${totalCredit.toFixed(2)}`;
            document.getElementById('tableTotalPayments').textContent = `$${totalPayments.toFixed(2)}`;
            document.getElementById('tableOutstandingBalance').textContent = `$${totalOutstanding.toFixed(2)}`;
        }
    });

    // Initialize date inputs with current month range
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    startDate.valueAsDate = firstDay;
    endDate.valueAsDate = lastDay;

    // Load territories
    loadTerritories();

    generateReportBtn.addEventListener('click', loadReport);
    document.getElementById('downloadReport').addEventListener('click', downloadReport);

    async function loadTerritories() {
        try {
            console.log('Loading territories...');
            const response = await fetch('/api/territories');
            if (!response.ok) {
                throw new Error('Failed to load territories');
            }

            const territories = await response.json();
            territorySelect.innerHTML = `
                <option value="">All Territories</option>
                ${territories.map(t => `<option value="${t}">${t}</option>`).join('')}
            `;
            console.log('Territories loaded successfully');
        } catch (error) {
            console.error('Error loading territories:', error);
            showError('Failed to load territories: ' + error.message);
        }
    }

    async function loadReport() {
        try {
            console.log('Loading report...');
            const params = new URLSearchParams({
                start_date: startDate.value,
                end_date: endDate.value,
                territory: territorySelect.value
            });

            const response = await fetch(`/api/reports?${params}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load report');
            }

            const data = await response.json();
            reportsTable.clear().rows.add(data.orders).draw();
            updateSummary(data.summary);
            console.log('Report loaded successfully');
        } catch (error) {
            console.error('Error loading report:', error);
            showError('Failed to load report: ' + error.message);
            reportsTable.clear().draw();
            clearSummary();
        }
    }

    function updateSummary(summary) {
        document.getElementById('totalOrders').textContent = summary.total_orders;
        document.getElementById('totalRevenue').textContent = `$${summary.total_revenue.toFixed(2)}`;
        document.getElementById('totalCases').textContent = summary.total_cases;
        document.getElementById('outstandingBalance').textContent = `$${summary.outstanding_balance.toFixed(2)}`;
    }

    function clearSummary() {
        document.getElementById('totalOrders').textContent = '0';
        document.getElementById('totalRevenue').textContent = '$0.00';
        document.getElementById('totalCases').textContent = '0';
        document.getElementById('outstandingBalance').textContent = '$0.00';
    }

    async function downloadReport() {
        try {
            console.log('Downloading report...');
            const params = new URLSearchParams({
                start_date: startDate.value,
                end_date: endDate.value,
                territory: territorySelect.value
            });
            
            const response = await fetch(`/download_report?${params}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to download report');
            }

            // Create a blob from the PDF stream
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${startDate.value}_${endDate.value}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('Report downloaded successfully');
            showSuccess('Report downloaded successfully');
        } catch (error) {
            console.error('Error downloading report:', error);
            showError('Failed to download report: ' + error.message);
        }
    }

    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.card').insertBefore(alertDiv, document.querySelector('.card-body'));
        setTimeout(() => alertDiv.remove(), 5000);
    }

    function showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.card').insertBefore(alertDiv, document.querySelector('.card-body'));
        setTimeout(() => alertDiv.remove(), 3000);
    }

    // Load initial report
    loadReport();
});
