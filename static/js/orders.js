document.addEventListener('DOMContentLoaded', function() {
    const ordersTable = $('#ordersTable').DataTable({
        dom: '<"row mb-3"<"col-md-6"B><"col-md-6"f>>rt<"row"<"col-md-6"l><"col-md-6"p>>',
        buttons: [
            {
                text: 'Reset Filters',
                className: 'btn btn-secondary',
                action: function () {
                    $('#customerFilter').val('');
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
            { 
                data: 'total_cases',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cases-input" 
                               value="${data}" min="0" style="width: 80px">`;
                    }
                    return data;
                }
            },
            { 
                data: 'total_cost',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cost-input" 
                               value="${parseFloat(data).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_cash',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input cash-input" 
                               value="${parseFloat(data).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_check',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input check-input" 
                               value="${parseFloat(data).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_credit',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input credit-input" 
                               value="${parseFloat(data).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data).toFixed(2)}`;
                }
            },
            {
                data: 'payment_received',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            {
                data: 'driver_expense',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            {
                data: 'id',
                render: function(data, type, row) {
                    if (row.isEditable) {
                        return `<button class="btn btn-sm btn-primary edit-order" data-id="${data}">Edit</button>`;
                    }
                    return `<button class="btn btn-sm btn-secondary view-order" data-id="${data}">View</button>`;
                }
            }
        ],
        createdRow: function(row, data) {
            if (!data.isEditable) {
                $(row).addClass('text-muted');
            }
        }
    });

    // Add filter controls above the table
    $('.card-body').prepend(`
        <div class="row mb-3">
            <div class="col-md-4">
                <select id="customerFilter" class="form-select">
                    <option value="">All Customers</option>
                </select>
            </div>
            <div class="col-md-8">
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

    // Event delegation for input changes in the table
    $('#ordersTable').on('change', 'input', function() {
        const row = $(this).closest('tr');
        const data = ordersTable.row(row).data();
        const updatedData = collectRowData(row, data);
        
        fetch('/api/orders/' + data.id, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        })
        .then(response => response.json())
        .then(() => {
            loadOrders();
        });
    });

    function collectRowData(row, originalData) {
        return {
            id: originalData.id,
            total_cases: parseInt(row.find('.cases-input').val()) || 0,
            total_cost: parseFloat(row.find('.cost-input').val()) || 0,
            payment_cash: parseFloat(row.find('.cash-input').val()) || 0,
            payment_check: parseFloat(row.find('.check-input').val()) || 0,
            payment_credit: parseFloat(row.find('.credit-input').val()) || 0
        };
    }

    // Save order
    document.getElementById('saveOrder').addEventListener('click', function() {
        const orderData = {
            customer_id: document.getElementById('customerId').value,
            delivery_date: document.getElementById('deliveryDate').value,
            total_cases: parseInt(document.getElementById('totalCases').value),
            total_cost: parseFloat(document.getElementById('totalCost').value),
            payment_cash: parseFloat(document.getElementById('paymentCash').value) || 0,
            payment_check: parseFloat(document.getElementById('paymentCheck').value) || 0,
            payment_credit: parseFloat(document.getElementById('paymentCredit').value) || 0,
            payment_received: parseFloat(document.getElementById('paymentReceived').value) || 0,
            driver_expense: parseFloat(document.getElementById('driverExpense').value) || 0
        };

        fetch('/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        })
        .then(response => response.json())
        .then(() => {
            $('#orderModal').modal('hide');
            loadOrders();
        })
        .catch(error => {
            console.error('Error saving order:', error);
            alert('Error saving order. Please try again.');
        });
    });

    // Edit order
    $('#ordersTable').on('click', '.edit-order', function() {
        const row = ordersTable.row($(this).parents('tr')).data();
        populateModal(row);
    });

    // View order (read-only)
    $('#ordersTable').on('click', '.view-order', function() {
        const row = ordersTable.row($(this).parents('tr')).data();
        populateModal(row, true);
    });

    function populateModal(data, readOnly = false) {
        document.getElementById('orderId').value = data.id;
        document.getElementById('customerId').value = data.customer_id;
        document.getElementById('deliveryDate').value = new Date(data.delivery_date).toISOString().split('T')[0];
        document.getElementById('totalCases').value = data.total_cases;
        document.getElementById('totalCost').value = data.total_cost;
        document.getElementById('paymentCash').value = data.payment_cash || 0;
        document.getElementById('paymentCheck').value = data.payment_check || 0;
        document.getElementById('paymentCredit').value = data.payment_credit || 0;
        document.getElementById('paymentReceived').value = data.payment_received || 0;
        document.getElementById('driverExpense').value = data.driver_expense || 0;

        // Handle read-only mode
        const inputs = document.querySelectorAll('#orderForm input, #orderForm select');
        inputs.forEach(input => {
            input.disabled = readOnly;
        });
        document.getElementById('saveOrder').style.display = readOnly ? 'none' : 'block';

        $('#orderModal').modal('show');
    }

    // Reset form when modal is opened for new order
    $('#orderModal').on('show.bs.modal', function(e) {
        if (!e.relatedTarget?.closest('.edit-order') && !e.relatedTarget?.closest('.view-order')) {
            document.getElementById('orderForm').reset();
            document.getElementById('orderId').value = '';
            document.getElementById('deliveryDate').valueAsDate = new Date();
            document.getElementById('paymentCash').value = '0';
            document.getElementById('paymentCheck').value = '0';
            document.getElementById('paymentCredit').value = '0';
            document.getElementById('paymentReceived').value = '0';
            document.getElementById('driverExpense').value = '0';

            // Enable all inputs for new order
            const inputs = document.querySelectorAll('#orderForm input, #orderForm select');
            inputs.forEach(input => {
                input.disabled = false;
            });
            document.getElementById('saveOrder').style.display = 'block';
        }
    });

    function loadOrders() {
        const startDate = document.getElementById('dateRangeStart').value;
        const endDate = document.getElementById('dateRangeEnd').value;
        const dateToUse = startDate || endDate || new Date().toISOString().split('T')[0];
        const today = new Date().toISOString().split('T')[0];
        
        fetch(`/api/orders/${dateToUse}`)
            .then(response => response.json())
            .then(data => {
                // Mark orders as editable if they're for today
                const processedData = data.map(order => ({
                    ...order,
                    isEditable: order.delivery_date.split('T')[0] === today
                }));
                ordersTable.clear().rows.add(processedData).draw();
            });
    }

    // Initial load
    loadOrders();
});
