document.addEventListener('DOMContentLoaded', function() {
    const ordersTable = $('#ordersTable').DataTable({
        columns: [
            { data: 'customer_name' },
            { 
                data: 'order_date',
                render: function(data) {
                    return new Date(data).toLocaleDateString();
                }
            },
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
                data: 'payment_received',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            {
                data: 'driver_expense',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            { data: 'status' },
            {
                data: 'id',
                render: function(data, type, row) {
                    return `
                        <button class="btn btn-sm btn-primary edit-order" data-id="${data}">Edit</button>
                        <button class="btn btn-sm btn-secondary update-status" data-id="${data}">
                            ${row.status === 'pending' ? 'Mark Delivered' : 'Update Status'}
                        </button>
                    `;
                }
            }
        ]
    });

    // Load customers for the dropdown
    fetch('/api/customers')
        .then(response => response.json())
        .then(customers => {
            const select = document.getElementById('customerId');
            select.innerHTML = customers.map(c => 
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
        });

    // Calculate total cost when cases or cost per case changes
    document.getElementById('totalCases').addEventListener('input', calculateTotal);
    document.getElementById('costPerCase').addEventListener('input', calculateTotal);

    // Calculate total payment when any payment field changes
    document.querySelectorAll('.payment-input').forEach(input => {
        input.addEventListener('input', calculateTotalPayment);
    });

    function calculateTotal() {
        const cases = document.getElementById('totalCases').value || 0;
        const costPerCase = document.getElementById('costPerCase').value || 0;
        const total = cases * costPerCase;
        document.getElementById('totalCost').value = total.toFixed(2);
        validatePayments();
    }

    function calculateTotalPayment() {
        const cash = parseFloat(document.getElementById('paymentCash').value) || 0;
        const check = parseFloat(document.getElementById('paymentCheck').value) || 0;
        const credit = parseFloat(document.getElementById('paymentCredit').value) || 0;
        const total = cash + check + credit;
        document.getElementById('paymentReceived').value = total.toFixed(2);
        validatePayments();
    }

    function validatePayments() {
        const totalCost = parseFloat(document.getElementById('totalCost').value) || 0;
        const totalPayment = parseFloat(document.getElementById('paymentReceived').value) || 0;
        const saveButton = document.getElementById('saveOrder');
        
        if (totalPayment > totalCost) {
            alert('Total payment cannot exceed total cost');
            saveButton.disabled = true;
        } else {
            saveButton.disabled = false;
        }
    }

    // Save order
    document.getElementById('saveOrder').addEventListener('click', function() {
        const orderId = document.getElementById('orderId').value;
        const orderData = {
            customer_id: document.getElementById('customerId').value,
            delivery_date: document.getElementById('deliveryDate').value,
            total_cases: parseInt(document.getElementById('totalCases').value),
            total_cost: parseFloat(document.getElementById('totalCost').value),
            payment_cash: parseFloat(document.getElementById('paymentCash').value) || 0,
            payment_check: parseFloat(document.getElementById('paymentCheck').value) || 0,
            payment_credit: parseFloat(document.getElementById('paymentCredit').value) || 0,
            payment_received: parseFloat(document.getElementById('paymentReceived').value) || 0,
            driver_expense: parseFloat(document.getElementById('driverExpense').value) || 0,
            is_one_time_delivery: document.getElementById('isOneTimeDelivery').checked,
            status: document.getElementById('orderStatus').value
        };

        const method = orderId ? 'PUT' : 'POST';
        if (orderId) orderData.id = orderId;

        fetch('/orders', {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        })
        .then(response => response.json())
        .then(() => {
            $('#orderModal').modal('hide');
            loadOrders();
        });
    });

    // Edit order
    $('#ordersTable').on('click', '.edit-order', function() {
        const row = ordersTable.row($(this).parents('tr')).data();
        document.getElementById('orderId').value = row.id;
        document.getElementById('customerId').value = row.customer_id;
        document.getElementById('deliveryDate').value = new Date(row.delivery_date).toISOString().split('T')[0];
        document.getElementById('totalCases').value = row.total_cases;
        document.getElementById('totalCost').value = row.total_cost;
        document.getElementById('paymentCash').value = row.payment_cash || 0;
        document.getElementById('paymentCheck').value = row.payment_check || 0;
        document.getElementById('paymentCredit').value = row.payment_credit || 0;
        document.getElementById('paymentReceived').value = row.payment_received || 0;
        document.getElementById('driverExpense').value = row.driver_expense || 0;
        document.getElementById('isOneTimeDelivery').checked = row.is_one_time_delivery;
        document.getElementById('orderStatus').value = row.status;
        $('#orderModal').modal('show');
    });

    // Update status
    $('#ordersTable').on('click', '.update-status', function() {
        const row = ordersTable.row($(this).parents('tr')).data();
        const newStatus = row.status === 'pending' ? 'delivered' : 'pending';
        
        fetch('/orders', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: row.id,
                status: newStatus
            })
        })
        .then(response => response.json())
        .then(() => {
            loadOrders();
        });
    });

    // Reset form when modal is opened for new order
    $('#orderModal').on('show.bs.modal', function(e) {
        if (!e.relatedTarget?.closest('.edit-order')) {
            document.getElementById('orderForm').reset();
            document.getElementById('orderId').value = '';
            document.getElementById('deliveryDate').valueAsDate = new Date();
            document.getElementById('paymentCash').value = '0';
            document.getElementById('paymentCheck').value = '0';
            document.getElementById('paymentCredit').value = '0';
            document.getElementById('paymentReceived').value = '0';
            document.getElementById('driverExpense').value = '0';
            document.getElementById('isOneTimeDelivery').checked = false;
        }
    });

    function loadOrders() {
        const today = new Date().toISOString().split('T')[0];
        fetch(`/api/orders/${today}`)
            .then(response => response.json())
            .then(data => {
                ordersTable.clear().rows.add(data).draw();
            });
    }

    // Initial load
    loadOrders();
});
