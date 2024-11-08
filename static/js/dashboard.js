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
                               value="${data || 0}" min="0" style="width: 80px">`;
                    }
                    return data || 0;
                }
            },
            { 
                data: 'total_cost',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cost-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_cash',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input cash-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_check',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input check-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_credit',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input credit-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            {
                data: 'payment_received',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
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
        loadDailyDriverExpense();
        updateAddOrderButton();
    });

    document.getElementById('saveDriverExpense').addEventListener('click', saveDailyDriverExpense);

    // Event delegation for input changes in the table
    $('#ordersTable').on('change', 'input', function() {
        const row = $(this).closest('tr');
        const data = ordersTable.row(row).data();
        const updatedData = collectRowData(row, data);
        
        updateOrder(data.id, updatedData);
    });

    async function updateOrder(orderId, updatedData) {
        try {
            const response = await fetch(`/api/orders/${orderId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to update order');
            }

            await loadOrders(); // Reload to refresh totals
        } catch (error) {
            console.error('Error updating order:', error);
            showError('Failed to update order: ' + error.message);
        }
    }

    // Load customers for the modal
    fetch('/api/customers')
        .then(response => {
            if (!response.ok) throw new Error('Failed to load customers');
            return response.json();
        })
        .then(customers => {
            const customerOptions = customers.map(c => 
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
            document.getElementById('customerId').innerHTML = customerOptions;
        })
        .catch(error => {
            console.error('Error loading customers:', error);
            showError('Failed to load customers: ' + error.message);
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
    document.getElementById('saveOrder').addEventListener('click', async function() {
        try {
            const orderData = {
                customer_id: document.getElementById('customerId').value,
                delivery_date: deliveryDate.value
            };

            const response = await fetch('/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create order');
            }

            $('#orderModal').modal('hide');
            await loadOrders();
        } catch (error) {
            console.error('Error saving order:', error);
            showError('Failed to create order: ' + error.message);
        }
    });

    async function loadOrders() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const response = await fetch(`/api/orders/${deliveryDate.value}`);
            
            if (!response.ok) {
                throw new Error('Failed to load orders');
            }

            const data = await response.json();
            // Mark orders as editable if they're for today
            const processedData = data.map(order => ({
                ...order,
                isEditable: deliveryDate.value === today
            }));
            
            ordersTable.clear().rows.add(processedData).draw();
            updateTotals(processedData);
        } catch (error) {
            console.error('Error loading orders:', error);
            showError('Failed to load orders: ' + error.message);
        }
    }

    async function loadDailyDriverExpense() {
        try {
            const response = await fetch(`/api/daily_driver_expense/${deliveryDate.value}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    // Not an error, just no expense set yet
                    dailyDriverExpense.value = 0;
                    return;
                }
                throw new Error('Failed to load driver expense');
            }

            const data = await response.json();
            dailyDriverExpense.value = data.amount || 0;
            updateTotals(ordersTable.data());
        } catch (error) {
            console.error('Error loading driver expense:', error);
            dailyDriverExpense.value = 0;
            showError('Failed to load driver expense: ' + error.message);
        }
    }

    async function saveDailyDriverExpense() {
        try {
            const amount = parseFloat(dailyDriverExpense.value) || 0;
            const response = await fetch('/api/daily_driver_expense', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: deliveryDate.value,
                    amount: amount
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save driver expense');
            }

            updateTotals(ordersTable.data());
            showSuccess('Driver expense saved successfully');
        } catch (error) {
            console.error('Error saving driver expense:', error);
            showError('Failed to save driver expense: ' + error.message);
        }
    }

    function updateTotals(orders) {
        const totals = orders.reduce((acc, order) => {
            acc.cases += parseInt(order.total_cases) || 0;
            acc.cost += parseFloat(order.total_cost) || 0;
            acc.cashPayments += parseFloat(order.payment_cash) || 0;
            acc.checkPayments += parseFloat(order.payment_check) || 0;
            acc.creditPayments += parseFloat(order.payment_credit) || 0;
            acc.totalPayments += parseFloat(order.payment_received) || 0;
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

    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.card'));
        setTimeout(() => alertDiv.remove(), 5000);
    }

    function showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.card'));
        setTimeout(() => alertDiv.remove(), 3000);
    }

    // Initial updates
    updateAddOrderButton();
    loadDailyDriverExpense();
});
