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
                    try {
                        return data ? new Date(data).toLocaleDateString() : '';
                    } catch (error) {
                        console.error('Error formatting date:', error);
                        return data || '';
                    }
                }
            },
            { 
                data: 'total_cases',
                render: value => value || 0
            },
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
                data: null,
                render: function(data) {
                    const balance = parseFloat(data.total_cost || 0) - parseFloat(data.payment_received || 0);
                    return `$${balance.toFixed(2)}`;
                }
            },
            {
                data: null,
                render: function(data) {
                    const balance = parseFloat(data.total_cost || 0) - parseFloat(data.payment_received || 0);
                    return balance > 0 ? 'OPEN' : 'CLOSED';
                }
            },
            {
                data: 'id',
                render: function(data) {
                    return `
                        <button class="btn btn-sm btn-primary edit-order" data-id="${data}">Edit</button>
                        <a href="/invoice/${data}" class="btn btn-sm btn-info">Invoice</a>
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
                    <option value="OPEN">Open</option>
                    <option value="CLOSED">Closed</option>
                </select>
            </div>
        </div>
    `);

    // Load customers for filters and modal
    loadCustomers();

    // Add filter event listeners
    $('#customerFilter').on('change', function() {
        ordersTable.column(0).search($(this).find('option:selected').text()).draw();
    });

    $('#statusFilter').on('change', function() {
        ordersTable.column(8).search(this.value).draw();
    });

    // Save order
    document.getElementById('saveOrder').addEventListener('click', async function() {
        try {
            console.log('Saving order...');
            const orderData = collectOrderData();
            
            if (!orderData.customer_id) {
                throw new Error('Customer is required');
            }

            const method = orderData.id ? 'PUT' : 'POST';
            const url = orderData.id ? `/api/orders/${orderData.id}` : '/orders';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save order');
            }

            $('#orderModal').modal('hide');
            await loadOrders();
            showSuccess('Order saved successfully');
        } catch (error) {
            console.error('Error saving order:', error);
            showError('Failed to save order: ' + error.message);
        }
    });

    // Edit order
    $('#ordersTable').on('click', '.edit-order', function() {
        try {
            const row = ordersTable.row($(this).parents('tr')).data();
            if (!row) {
                throw new Error('Order data not found');
            }
            populateForm(row);
            $('#orderModal').modal('show');
        } catch (error) {
            console.error('Error editing order:', error);
            showError('Failed to edit order: ' + error.message);
        }
    });

    // Reset form when modal is opened for new order
    $('#orderModal').on('show.bs.modal', function(e) {
        if (!e.relatedTarget?.closest('.edit-order')) {
            document.getElementById('orderForm').reset();
            document.getElementById('orderId').value = '';
            document.getElementById('deliveryDate').valueAsDate = new Date();
        }
    });

    async function loadOrders() {
        try {
            console.log('Loading orders...');
            const response = await fetch('/api/orders');
            if (!response.ok) {
                throw new Error('Failed to load orders');
            }

            const orders = await response.json();
            ordersTable.clear().rows.add(orders).draw();
            console.log('Orders loaded successfully:', orders.length, 'orders');
        } catch (error) {
            console.error('Error loading orders:', error);
            showError('Failed to load orders: ' + error.message);
            ordersTable.clear().draw();
        }
    }

    async function loadCustomers() {
        try {
            console.log('Loading customers...');
            const response = await fetch('/api/customers');
            if (!response.ok) {
                throw new Error('Failed to load customers');
            }

            const customers = await response.json();
            const customerOptions = customers.map(c => 
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
            
            document.getElementById('customerId').innerHTML = customerOptions;
            document.getElementById('customerFilter').innerHTML += customerOptions;
            console.log('Customers loaded successfully:', customers.length, 'customers');
        } catch (error) {
            console.error('Error loading customers:', error);
            showError('Failed to load customers: ' + error.message);
        }
    }

    function collectOrderData() {
        const data = {
            id: document.getElementById('orderId').value,
            customer_id: document.getElementById('customerId').value,
            delivery_date: document.getElementById('deliveryDate').value,
            total_cases: parseInt(document.getElementById('totalCases').value) || 0,
            total_cost: parseFloat(document.getElementById('totalCost').value) || 0,
            payment_cash: parseFloat(document.getElementById('paymentCash').value) || 0,
            payment_check: parseFloat(document.getElementById('paymentCheck').value) || 0,
            payment_credit: parseFloat(document.getElementById('paymentCredit').value) || 0
        };

        // Validate required fields
        if (!data.customer_id) {
            throw new Error('Customer is required');
        }
        if (!data.delivery_date) {
            throw new Error('Delivery date is required');
        }

        return data;
    }

    function populateForm(data) {
        try {
            document.getElementById('orderId').value = data.id || '';
            document.getElementById('customerId').value = data.customer_id || '';
            document.getElementById('deliveryDate').value = data.delivery_date ? 
                new Date(data.delivery_date).toISOString().split('T')[0] : '';
            document.getElementById('totalCases').value = data.total_cases || 0;
            document.getElementById('totalCost').value = data.total_cost || 0;
            document.getElementById('paymentCash').value = data.payment_cash || 0;
            document.getElementById('paymentCheck').value = data.payment_check || 0;
            document.getElementById('paymentCredit').value = data.payment_credit || 0;
        } catch (error) {
            console.error('Error populating form:', error);
            showError('Failed to load order details: ' + error.message);
        }
    }

    function showError(message) {
        console.error(message);
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
        console.log(message);
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.card').insertBefore(alertDiv, document.querySelector('.card-body'));
        setTimeout(() => alertDiv.remove(), 3000);
    }

    // Load initial data
    loadOrders();
});
