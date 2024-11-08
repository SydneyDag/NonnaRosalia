document.addEventListener('DOMContentLoaded', function() {
    const ordersTable = $('#ordersTable').DataTable({
        dom: '<"row mb-3"<"col-md-6"B><"col-md-6"f>>rt<"row"<"col-md-6"l><"col-md-6"p>>',
        buttons: [
            {
                text: 'Reset Filters',
                className: 'btn btn-secondary',
                action: function () {
                    $('#customerFilter').val('');
                    $('#statusFilter').val('');
                    $('#dateRangeStart').val('');
                    $('#dateRangeEnd').val('');
                    ordersTable.search('').columns().search('').draw();
                    loadOrders();
                }
            }
        ],
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
                data: null,
                render: function(data) {
                    const balance = parseFloat(data.total_cost) - parseFloat(data.payment_received);
                    return `$${balance.toFixed(2)}`;
                }
            },
            {
                data: null,
                render: function(data) {
                    const balance = parseFloat(data.total_cost) - parseFloat(data.payment_received);
                    return balance > 0 ? 'open' : 'closed';
                }
            },
            {
                data: 'id',
                render: function(data) {
                    return `
                        <button class="btn btn-sm btn-primary edit-order" data-id="${data}">Edit</button>
                        <button class="btn btn-sm btn-info" onclick="window.location.href='/generate_invoice/${data}'">
                            Invoice
                        </button>
                    `;
                }
            }
        ]
    });

    // Add filter controls above the table
    $('.card-body').prepend(`
        <div class="row mb-3">
            <div class="col-md-3">
                <select id="customerFilter" class="form-select">
                    <option value="">All Customers</option>
                </select>
            </div>
            <div class="col-md-3">
                <select id="statusFilter" class="form-select">
                    <option value="">All Statuses</option>
                    <option value="open">Open</option>
                    <option value="closed">Closed</option>
                </select>
            </div>
            <div class="col-md-6">
                <div class="input-group">
                    <input type="date" class="form-control" id="dateRangeStart">
                    <span class="input-group-text">to</span>
                    <input type="date" class="form-control" id="dateRangeEnd">
                </div>
            </div>
        </div>
    `);

    // Initialize date inputs
    const now = new Date();
    document.getElementById('dateRangeStart').valueAsDate = now;
    document.getElementById('dateRangeEnd').valueAsDate = now;

    // Load customers for filters and modal
    fetch('/api/customers')
        .then(response => response.json())
        .then(customers => {
            const customerOptions = customers.map(c => 
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
            
            document.getElementById('customerId').innerHTML = customerOptions;
            document.getElementById('customerFilter').innerHTML += customerOptions;
        });

    // Add filter event listeners
    $('#customerFilter').on('change', function() {
        ordersTable.column(0).search($(this).find('option:selected').text()).draw();
    });

    $('#statusFilter').on('change', function() {
        ordersTable.column(7).search(this.value).draw();
    });

    $('#dateRangeStart, #dateRangeEnd').on('change', function() {
        loadOrders();
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
            is_one_time_delivery: document.getElementById('isOneTimeDelivery').checked
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
        document.getElementById('isOneTimeDelivery').checked = row.is_one_time_delivery;
        $('#orderModal').modal('show');
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
            document.getElementById('isOneTimeDelivery').checked = false;
        }
    });

    function loadOrders() {
        const startDate = document.getElementById('dateRangeStart').value;
        const endDate = document.getElementById('dateRangeEnd').value;
        const dateToUse = startDate || endDate || new Date().toISOString().split('T')[0];
        
        fetch(`/api/orders/${dateToUse}`)
            .then(response => response.json())
            .then(data => {
                ordersTable.clear().rows.add(data).draw();
            });
    }

    // Initial load
    loadOrders();
});
