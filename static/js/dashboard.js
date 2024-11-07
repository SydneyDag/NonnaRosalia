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
        ]
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
            acc.cost += order.total_cost;
            acc.payments += order.payment_received;
            return acc;
        }, { cases: 0, cost: 0, payments: 0 });

        document.getElementById('totalCases').textContent = totals.cases;
        document.getElementById('totalCost').textContent = `$${totals.cost.toFixed(2)}`;
        document.getElementById('totalPayments').textContent = `$${totals.payments.toFixed(2)}`;
    }
});
