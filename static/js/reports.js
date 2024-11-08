document.addEventListener('DOMContentLoaded', function() {
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const territorySelect = document.getElementById('territory');
    const generateReportBtn = document.getElementById('generateReport');
    
    // Create alert container at the start
    const cardBody = document.querySelector('.card-body');
    const alertContainer = document.createElement('div');
    alertContainer.className = 'alert-container mb-3';
    if (cardBody) {
        cardBody.insertBefore(alertContainer, cardBody.firstChild);
    }
    
    const reportsTable = $('#reportsTable').DataTable({
        columns: [
            { 
                data: 'delivery_date',
                render: function(data) {
                    try {
                        return data ? new Date(data).toLocaleDateString() : '';
                    } catch (error) {
                        console.error('Error formatting date:', error);
                        return data || '';
                    }
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
            try {
                const api = this.api();

                // Calculate column totals
                const totalCases = api.column(1).data().reduce((a, b) => a + (parseInt(b) || 0), 0);
                const totalCost = api.column(2).data().reduce((a, b) => a + (parseFloat(b) || 0), 0);
                const totalCash = api.column(3).data().reduce((a, b) => a + (parseFloat(b) || 0), 0);
                const totalCheck = api.column(4).data().reduce((a, b) => a + (parseFloat(b) || 0), 0);
                const totalCredit = api.column(5).data().reduce((a, b) => a + (parseFloat(b) || 0), 0);
                const totalPayments = api.column(6).data().reduce((a, b) => a + (parseFloat(b) || 0), 0);
                const totalOutstanding = api.column(7).data().reduce((a, b) => a + (parseFloat(b) || 0), 0);

                // Update footer cells
                const updateElement = (id, value) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = typeof value === 'number' ? 
                            (id.includes('Cases') ? value : `$${value.toFixed(2)}`) : 
                            (value || '0');
                    }
                };

                updateElement('tableTotalCases', totalCases);
                updateElement('tableTotalCost', totalCost);
                updateElement('tableTotalCash', totalCash);
                updateElement('tableTotalCheck', totalCheck);
                updateElement('tableTotalCredit', totalCredit);
                updateElement('tableTotalPayments', totalPayments);
                updateElement('tableOutstandingBalance', totalOutstanding);
            } catch (error) {
                console.error('Error calculating totals:', error);
            }
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
                start_date: startDate.value || new Date().toISOString().split('T')[0],
                end_date: endDate.value || new Date().toISOString().split('T')[0],
                territory: territorySelect.value
            });

            const response = await fetch(`/api/reports?${params}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load report data');
            }

            const data = await response.json();
            if (!data || !data.orders) {
                throw new Error('Invalid report data received');
            }

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
        try {
            if (!summary) {
                throw new Error('Invalid summary data');
            }

            const updateElement = (id, value, isMonetary = true) => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = isMonetary ? 
                        `$${parseFloat(value || 0).toFixed(2)}` : 
                        (value || 0).toString();
                }
            };

            updateElement('totalOrders', summary.total_orders, false);
            updateElement('totalRevenue', summary.total_revenue);
            updateElement('totalCases', summary.total_cases, false);
            updateElement('outstandingBalance', summary.outstanding_balance);
        } catch (error) {
            console.error('Error updating summary:', error);
            showError('Failed to update summary: ' + error.message);
        }
    }

    function clearSummary() {
        const elements = ['totalOrders', 'totalRevenue', 'totalCases', 'outstandingBalance'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = id.includes('total_orders') || id.includes('total_cases') ? 
                    '0' : '$0.00';
            }
        });
    }

    function showError(message) {
        try {
            if (!alertContainer) {
                console.error('Alert container not found');
                return;
            }

            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Clear existing alerts
            while (alertContainer.firstChild) {
                alertContainer.removeChild(alertContainer.firstChild);
            }
            
            alertContainer.appendChild(alertDiv);
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode === alertContainer) {
                    alertDiv.remove();
                }
            }, 5000);
        } catch (error) {
            console.error('Error showing alert:', error);
        }
    }

    function showSuccess(message) {
        try {
            if (!alertContainer) {
                console.error('Alert container not found');
                return;
            }

            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Clear existing alerts
            while (alertContainer.firstChild) {
                alertContainer.removeChild(alertContainer.firstChild);
            }
            
            alertContainer.appendChild(alertDiv);
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode === alertContainer) {
                    alertDiv.remove();
                }
            }, 3000);
        } catch (error) {
            console.error('Error showing alert:', error);
        }
    }

    // Load initial report
    loadReport();
});
