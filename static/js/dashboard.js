document.addEventListener('DOMContentLoaded', function() {
    const deliveryDate = document.getElementById('deliveryDate');
    const ordersTable = $('#ordersTable').DataTable({
        columns: [
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
            { data: 'status' }
        ],
        order: [[0, 'asc']]
    });

    deliveryDate.valueAsDate = new Date();
    loadOrders();

    deliveryDate.addEventListener('change', loadOrders);

    function loadOrders() {
        fetch(`/api/orders/${deliveryDate.value}`)
            .then(response => response.json())
            .then(data => {
                ordersTable.clear().rows.add(data).draw();
                updateTotals(data);
            });
    }

    function updateTotals(orders) {
        const totals = orders.reduce((acc, order) => {
            acc.cases += order.total_cases;
            acc.cost += parseFloat(order.total_cost);
            acc.payments += parseFloat(order.payment_received);
            acc.driverExpenses += parseFloat(order.driver_expense);
            return acc;
        }, { cases: 0, cost: 0, payments: 0, driverExpenses: 0 });

        document.getElementById('totalCases').textContent = totals.cases;
        document.getElementById('totalCost').textContent = `$${totals.cost.toFixed(2)}`;
        document.getElementById('totalPayments').textContent = `$${totals.payments.toFixed(2)}`;
        
        // Update or create driver expenses total
        let driverExpenseCell = document.getElementById('totalDriverExpenses');
        if (!driverExpenseCell) {
            const row = document.querySelector('#ordersTable tfoot tr');
            const cell = document.createElement('th');
            cell.id = 'totalDriverExpenses';
            row.insertBefore(cell, row.lastElementChild);
        }
        document.getElementById('totalDriverExpenses').textContent = `$${totals.driverExpenses.toFixed(2)}`;
    }
});
