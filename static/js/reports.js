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
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            { 
                data: 'payment_cash',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            { 
                data: 'payment_check',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            { 
                data: 'payment_credit',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            { 
                data: 'payment_received',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            {
                data: 'outstanding',
                render: value => `$${parseFloat(value).toFixed(2)}`
            }
        ],
        order: [[0, 'desc']],
        footerCallback: function(row, data, start, end, display) {
            const api = this.api();

            // Calculate column totals
            const totalCases = api.column(1).data().reduce((a, b) => a + b, 0);
            const totalCost = api.column(2).data().reduce((a, b) => a + parseFloat(b), 0);
            const totalCash = api.column(3).data().reduce((a, b) => a + parseFloat(b), 0);
            const totalCheck = api.column(4).data().reduce((a, b) => a + parseFloat(b), 0);
            const totalCredit = api.column(5).data().reduce((a, b) => a + parseFloat(b), 0);
            const totalPayments = api.column(6).data().reduce((a, b) => a + parseFloat(b), 0);
            const totalOutstanding = api.column(7).data().reduce((a, b) => a + parseFloat(b), 0);

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

    // Load territories for the filter
    fetch('/api/territories')
        .then(response => response.json())
        .then(territories => {
            territorySelect.innerHTML += territories.map(t => 
                `<option value="${t}">${t}</option>`
            ).join('');
        });

    generateReportBtn.addEventListener('click', loadReport);
    document.getElementById('downloadReport').addEventListener('click', downloadReport);

    function loadReport() {
        const params = new URLSearchParams({
            start_date: startDate.value,
            end_date: endDate.value,
            territory: territorySelect.value
        });

        fetch(`/api/reports?${params}`)
            .then(response => response.json())
            .then(data => {
                reportsTable.clear().rows.add(data.orders).draw();
                updateSummary(data.summary);
            });
    }

    function updateSummary(summary) {
        document.getElementById('totalOrders').textContent = summary.total_orders;
        document.getElementById('totalRevenue').textContent = `$${summary.total_revenue.toFixed(2)}`;
        document.getElementById('totalCases').textContent = summary.total_cases;
        document.getElementById('outstandingBalance').textContent = `$${summary.outstanding_balance.toFixed(2)}`;
    }

    function downloadReport() {
        const params = new URLSearchParams({
            start_date: startDate.value,
            end_date: endDate.value,
            territory: territorySelect.value
        });
        
        window.location.href = `/download_report?${params}`;
    }

    // Load initial report
    loadReport();
});
