document.addEventListener('DOMContentLoaded', function() {
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const territorySelect = document.getElementById('territory');
    const generateReportBtn = document.getElementById('generateReport');
    
    const reportsTable = $('#reportsTable').DataTable({
        columns: [
            { 
                data: 'order_date',
                render: function(data) {
                    return new Date(data).toLocaleDateString();
                }
            },
            { data: 'territory' },
            { data: 'customer_name' },
            { data: 'total_cases' },
            { 
                data: 'total_cost',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            { 
                data: 'payment_received',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            {
                data: null,
                render: function(data) {
                    const outstanding = parseFloat(data.total_cost) - parseFloat(data.payment_received);
                    return `$${outstanding.toFixed(2)}`;
                }
            },
            { data: 'status' }
        ],
        order: [[0, 'desc']]
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

        // Update table footer
        document.getElementById('tableTotalCases').textContent = summary.total_cases;
        document.getElementById('tableTotalCost').textContent = `$${summary.total_revenue.toFixed(2)}`;
        document.getElementById('tableTotalPayments').textContent = `$${summary.total_payments.toFixed(2)}`;
        document.getElementById('tableOutstandingBalance').textContent = `$${summary.outstanding_balance.toFixed(2)}`;
    }

    // Load initial report
    loadReport();
});
