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
        loadDailyDriverExpense();
        updateAddOrderButton();
    });

    document.getElementById('saveDriverExpense').addEventListener('click', saveDailyDriverExpense);

    // Calculate total payment when any payment field changes
    document.querySelectorAll('.payment-input').forEach(input => {
        input.addEventListener('input', calculateTotalPayment);
    });

    // Event delegation for input changes in the table
    $('#ordersTable').on('change', 'input', function() {
        const row = $(this).closest('tr');
        const data = ordersTable.row(row).data();
        const updatedData = collectRowData(row, data);
        
        // Update the order via API
        fetch('/api/orders/' + data.id, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        })
        .then(response => response.json())
        .then(() => {
            loadOrders(); // Reload to refresh totals
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
            delivery_date: deliveryDate.value,
            total_cases: parseInt(document.getElementById('totalCases').value),
            total_cost: parseFloat(document.getElementById('totalCost').value),
            payment_cash: parseFloat(document.getElementById('paymentCash').value) || 0,
            payment_check: parseFloat(document.getElementById('paymentCheck').value) || 0,
            payment_credit: parseFloat(document.getElementById('paymentCredit').value) || 0,
            payment_received: parseFloat(document.getElementById('paymentReceived').value) || 0
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

    function loadOrders() {
        const today = new Date().toISOString().split('T')[0];
        fetch(`/api/orders/${deliveryDate.value}`)
            .then(response => response.json())
            .then(data => {
                // Mark orders as editable if they're for today
                const processedData = data.map(order => ({
                    ...order,
                    isEditable: deliveryDate.value === today
                }));
                ordersTable.clear().rows.add(processedData).draw();
                updateTotals(processedData);
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
    loadDailyDriverExpense();
});
