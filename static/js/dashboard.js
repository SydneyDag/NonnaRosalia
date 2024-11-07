document.addEventListener('DOMContentLoaded', function() {
    const deliveryDate = document.getElementById('deliveryDate');
    const dailyDriverExpense = document.getElementById('dailyDriverExpense');
    
    const ordersTable = $('#ordersTable').DataTable({
        columns: [
            { data: 'customer_name' },
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
            { data: 'status' }
        ],
        order: [[0, 'asc']]
    });

    // Initialize date picker with today's date
    deliveryDate.valueAsDate = new Date();
    loadOrders();

    // Event Listeners
    deliveryDate.addEventListener('change', () => {
        loadOrders();
        loadDailyDriverExpense();
    });

    document.getElementById('saveDriverExpense').addEventListener('click', saveDailyDriverExpense);

    function loadOrders() {
        fetch(`/api/orders/${deliveryDate.value}`)
            .then(response => response.json())
            .then(data => {
                ordersTable.clear().rows.add(data).draw();
                updateTotals(data);
            });
    }

    function loadDailyDriverExpense() {
        fetch(`/api/daily_driver_expense/${deliveryDate.value}`)
            .then(response => response.json())
            .then(data => {
                dailyDriverExpense.value = data.amount || 0;
                updateTotals(ordersTable.data());
            })
            .catch(() => {
                dailyDriverExpense.value = 0;
                updateTotals(ordersTable.data());
            });
    }

    function saveDailyDriverExpense() {
        const amount = parseFloat(dailyDriverExpense.value) || 0;
        fetch('/api/daily_driver_expense', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: deliveryDate.value,
                amount: amount
            })
        })
        .then(response => response.json())
        .then(() => {
            updateTotals(ordersTable.data());
        });
    }

    function updateTotals(orders) {
        const totals = orders.reduce((acc, order) => {
            acc.cases += order.total_cases;
            acc.cost += parseFloat(order.total_cost);
            acc.cashPayments += parseFloat(order.payment_cash);
            acc.checkPayments += parseFloat(order.payment_check);
            acc.creditPayments += parseFloat(order.payment_credit);
            acc.totalPayments += parseFloat(order.payment_received);
            return acc;
        }, { 
            cases: 0, 
            cost: 0, 
            cashPayments: 0,
            checkPayments: 0,
            creditPayments: 0,
            totalPayments: 0
        });

        // Update table totals
        document.getElementById('totalCases').textContent = totals.cases;
        document.getElementById('totalCost').textContent = `$${totals.cost.toFixed(2)}`;
        document.getElementById('totalCashPayments').textContent = `$${totals.cashPayments.toFixed(2)}`;
        document.getElementById('totalCheckPayments').textContent = `$${totals.checkPayments.toFixed(2)}`;
        document.getElementById('totalCreditPayments').textContent = `$${totals.creditPayments.toFixed(2)}`;
        document.getElementById('totalPayments').textContent = `$${totals.totalPayments.toFixed(2)}`;

        // Update daily summary
        const driverExpense = parseFloat(dailyDriverExpense.value) || 0;
        document.getElementById('totalDriverExpense').textContent = `$${driverExpense.toFixed(2)}`;
        
        const netIncome = totals.totalPayments - driverExpense;
        document.getElementById('netIncome').textContent = `$${netIncome.toFixed(2)}`;
    }

    // Initial load of driver expense
    loadDailyDriverExpense();
});
