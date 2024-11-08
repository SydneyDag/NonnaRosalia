document.addEventListener('DOMContentLoaded', function() {
    const deliveryDate = document.getElementById('deliveryDate');
    const dailyDriverExpense = document.getElementById('dailyDriverExpense');
    
    const ordersTable = $('#ordersTable').DataTable({
        columns: [
            { data: 'customer_name' },
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
            }
        ],
        createdRow: function(row, data) {
            if (!data.isEditable) {
                $(row).addClass('text-muted');
            }
        }
    });

    // Initialize date picker with today's date
    deliveryDate.valueAsDate = new Date();
    loadOrders();

    // Show/hide Add Order button based on selected date
    function updateAddOrderButton() {
        const today = new Date().toISOString().split('T')[0];
        const addOrderBtn = document.getElementById('addOrderBtn');
        if (addOrderBtn) {
            addOrderBtn.style.display = deliveryDate.value === today ? 'block' : 'none';
        }
    }

    // Event Listeners
    deliveryDate.addEventListener('change', () => {
        loadOrders();
        updateAddOrderButton();
    });

    // Event delegation for input changes in the table
    $('#ordersTable').on('change', 'input', function() {
        const row = $(this).closest('tr');
        const data = ordersTable.row(row).data();
        const updatedData = collectRowData(row, data);
        
        // Update the order via API
        fetch(`/api/orders/${data.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        })
        .then(response => response.json())
        .then(() => {
            loadOrders(); // Reload to refresh totals
        })
        .catch(error => {
            console.error('Error updating order:', error);
            showError('Error updating order. Please try again.');
        });
    });

    // Load customers for the modal
    fetch('/api/customers')
        .then(response => response.json())
        .then(customers => {
            const customerOptions = customers.map(c => 
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
            document.getElementById('customerId').innerHTML = customerOptions;
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

    // Save new order (simplified)
    document.getElementById('saveOrder').addEventListener('click', function() {
        const orderData = {
            customer_id: document.getElementById('customerId').value,
            delivery_date: deliveryDate.value
        };

        fetch('/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to create order');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.order) {
                // Add the new order directly to the table
                ordersTable.row.add(data.order).draw();
                updateTotals(ordersTable.data());
                $('#orderModal').modal('hide');
                
                showSuccess('Order created successfully');
            }
        })
        .catch(error => {
            console.error('Error saving order:', error);
            showError(error.message);
        });
    });

    function showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the table's parent card-body
        const cardBody = document.querySelector('#ordersTable').closest('.card-body');
        // Insert before the first child of card-body
        cardBody.insertBefore(alertDiv, cardBody.firstChild);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the table's parent card-body
        const cardBody = document.querySelector('#ordersTable').closest('.card-body');
        // Insert before the first child of card-body
        cardBody.insertBefore(alertDiv, cardBody.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    function loadOrders() {
        console.log('Loading orders for date:', deliveryDate.value);
        fetch(`/api/orders/${deliveryDate.value}`)
            .then(response => response.json())
            .then(data => {
                console.log('Orders loaded successfully');
                ordersTable.clear().rows.add(data).draw();
                updateTotals(data);
            })
            .catch(error => {
                console.error('Error loading orders:', error);
                showError('Error loading orders. Please try again.');
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

        // Update summary cards
        document.getElementById('totalCases').textContent = totals.cases;
        document.getElementById('totalCost').textContent = `$${totals.cost.toFixed(2)}`;
        document.getElementById('totalPayments').textContent = `$${totals.totalPayments.toFixed(2)}`;

        // Update table totals
        document.getElementById('tableTotalCases').textContent = totals.cases;
        document.getElementById('tableTotalCost').textContent = `$${totals.cost.toFixed(2)}`;
        document.getElementById('totalCashPayments').textContent = `$${totals.cashPayments.toFixed(2)}`;
        document.getElementById('totalCheckPayments').textContent = `$${totals.checkPayments.toFixed(2)}`;
        document.getElementById('totalCreditPayments').textContent = `$${totals.creditPayments.toFixed(2)}`;
        document.getElementById('tableTotalPayments').textContent = `$${totals.totalPayments.toFixed(2)}`;
    }

    // Initial updates
    updateAddOrderButton();
});
